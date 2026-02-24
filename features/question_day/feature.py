import logging
import datetime
from typing import Dict, List, Tuple

import discord
from discord import app_commands

from bot.core.checks import is_staff
from bot.db.feature_pool import FeaturePool

log = logging.getLogger(__name__)

FEATURE = {
    "slug": "question_day",
    "name": "Question of the Day",
    "description": "A feature that allows the bot to manage the question of the day.",
    "version": "1.0.0",
    "author": "Tryno",
    "requires_config": False,
    "permissions": ["send_messages", "embed_links"],
}


def register(tree: app_commands.CommandTree, config, database_interface: FeaturePool):
    group = app_commands.Group(name=FEATURE["slug"], description="Testing commands")

    @group.command(name="add", description="Add a question of the day")
    @is_staff()
    async def add_question_command(interaction: discord.Interaction, question: str, responses: str, correct_response: str):
        responses_list = responses.split(",")
        print(responses_list)
        await interaction.response.defer(ephemeral=True)
        result = await add_question(database_interface, question, responses_list, correct_response)
        if result:
            send_result = "Question added successfully!"
        else:
            send_result = "Failed to add question. Please check the logs for more details."
            log.error("Failed to add question through command.")
        await interaction.followup.send(send_result, ephemeral=True)

    @group.command(name="today", description="Get the question of the day")
    @is_staff()
    async def question_of_the_day_command(interaction: discord.Interaction):
        await interaction.response.defer()
        question, responses = await get_question_of_the_day(database_interface)
        if not question:
            await interaction.followup.send("No question of the day found.", ephemeral=True)
            return
        embed = discord.Embed(title="Question of the Day", description=question, color=discord.Color.blue())
        for response in responses:
            embed.add_field(name="Response", value=response["response_text"], inline=False)
        await interaction.followup.send(embed=embed)
    tree.add_command(group)


async def install(database_interface: FeaturePool) -> bool:
    try:
        await database_interface.add_table("questions", ["id SERIAL PRIMARY KEY", "question_text TEXT"])
        await database_interface.add_table(
            "responses",
            [
                "id SERIAL PRIMARY KEY",
                "question_id INT",
                "response_text TEXT",
                "is_correct BOOLEAN DEFAULT FALSE",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            ],
        )
        return True
    except Exception as e:
        log.error(f"Error initializing database tables: {e}")
        return False


async def add_question(
    database_interface: FeaturePool, question: str, responses: List[str], correct_response: str
) -> bool:
    try:
        inserted_id = await database_interface.insert("questions", ["question_text"], [question])
        log.info(f"Inserted question: {question} to database with ID: {inserted_id}")
        for response in responses:
            is_correct = response == correct_response
            await database_interface.insert(
                "responses", ["question_id", "response_text", "is_correct"], [inserted_id, response, is_correct]
            )
        return True
    except Exception as e:
        log.error(f"Error adding question: {e}")
        return False

async def get_question_of_the_day(database_interface: FeaturePool) -> Tuple[str, List[Dict[str, str]]]:
    try:
        # Fetch random question that hasn't been asked recently (calculate ratio with number of question available and number of question asked in the last 30 days, if ratio is above 0.5, allow to ask question that have been asked in the last 30 days)
        
        actual_date = datetime.datetime.now()
        number_of_questions = await database_interface.count("questions")
        number_of_recent_questions = await database_interface.count("questions", "asked_at >= CURRENT_DATE - INTERVAL '30 days'")
        ratio = number_of_recent_questions / number_of_questions if number_of_questions > 0 else 0
        
        print(f"Number of questions: {number_of_questions}, Number of recent questions: {number_of_recent_questions}, Ratio: {ratio}")
        
        if ratio > 0.5:
            # If more than 50% of questions have been asked in the last 30 days, allow to ask any question, even those that have been asked recently
            question = await database_interface.query(
                "WITH candite AS (SELECT id, question_text, asked_at FROM features.question_day_questions WHERE "
            )
        else:
            question = await database_interface.fetch_one("questions", 
                                                        ["id", "question_text"], 
                                                        condition="", 
                                                        order_by="id DESC")
        if not question:
            return None, []
        question_id = dict(question)["id"]
        
    
        
        question_text = dict(question)["question_text"]
        responses = await database_interface.fetch_all("responses", ["response_text"], "question_id = $1", question_id)
        return question_text, [dict(response) for response in responses]
    except Exception as e:
        log.error(f"Error fetching question of the day: {e}")
        return None, []