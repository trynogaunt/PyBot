import logging
import datetime
import time
from typing import Dict, List, Tuple
import asyncio

import discord
from discord import app_commands
from .view import DayView

from bot.core.checks import is_staff
from bot.db.feature_pool import FeaturePool

log = logging.getLogger(__name__)

FEATURE = {
    "slug": "question_day",
    "name": "Question of the Day",
    "description": "A feature that allows the bot to manage the question of the day.",
    "version": "1.0.0",
    "author": "Tryno",
    "requires_config": True,
    "permissions": ["send_messages", "embed_links"],
}


async def register(tree: app_commands.CommandTree, bot: discord.Client, config, database_interface: FeaturePool):
    group = app_commands.Group(name=FEATURE["slug"], description="Testing commands")

    @group.command(name="add", description="Add a question of the day")
    @is_staff()
    async def add_question_command(interaction: discord.Interaction, question: str, responses: str, correct_response: str):
        responses_list = responses.split(",")
        await interaction.response.defer(ephemeral=True)
        result = await add_question(database_interface, question, responses_list, correct_response)
        if result:
            send_result = "Question added successfully!"
        else:
            send_result = "Failed to add question. Please check the logs for more details."
            log.error("Failed to add question through command.")
        await interaction.followup.send(send_result, ephemeral=True)

 
    async def question_of_the_day_command(interaction: discord.Interaction):
        log = logging.getLogger(__name__)
        await interaction.response.defer()
        question, responses, correct_response = await get_question_of_the_day(database_interface)
        log.info(f"Question of the day: {question}")
        if not question:
            await interaction.followup.send("No question of the day found.", ephemeral=True)
            return
        try:
            embed = discord.Embed(title="Question of the Day", description=question, color=discord.Color.blue())
        except Exception as e:
            log.error(f"Error creating embed: {e}")
            await interaction.followup.send("An error occurred while creating the embed. Please try again later.", ephemeral=True)
            return
        for response in responses:
            log.info(f"Response: {response}")
        try:
            view = DayView(question_id=question, responses=responses, correct_response=correct_response)
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            log.error(f"Can't create view: {e}")
            await interaction.followup.send("An error occurred while creating the view. Please try again later.", ephemeral=True)
            return
        
        await asyncio.sleep(10)  # After predeterminate time send states and response
        correct_count, incorrect_count = view.count_responses()
        total_responses = correct_count + incorrect_count
        if total_responses == 0:
            await interaction.followup.send(f"No responses received for the question of the day. \n Correct response was: {correct_response['response_text']}", ephemeral=True)
            return
        await interaction.followup.send(f"Question of the Day has ended! \n Correct response was: {correct_response['response_text']} \n Total responses: {total_responses} \n Correct responses: {correct_count} \n Incorrect responses: {incorrect_count}", ephemeral=True)
        log.info(f"Correct responses: {correct_count}, Incorrect responses: {incorrect_count}")
            
    tree.add_command(group)

    async def planned_task(database_interface: FeaturePool, bot: discord.Client, config = config):
        try:
             while True:
                now = datetime.datetime.now()
                next_run = (now + datetime.timedelta(days=0)).replace(hour=0, minute=0, second=30, microsecond=0)
                wait_time = (next_run - now).total_seconds()
                log.info(f"Waiting for {wait_time} seconds until the next question of the day.")
                await asyncio.sleep(wait_time)
                await send_question_of_the_day(database_interface, bot, config)
        except Exception as e:
            log.error(f"Error in planned task: {e}")
    
    async def send_question_of_the_day(database_interface: FeaturePool, bot: discord.Client, config = config):
        print(config)
        for channel_id in config.get("channel_id", []):
            channel = await bot.fetch_channel(channel_id)
            print(channel)
            if not channel:
                log.error(f"Channel with ID {channel_id} not found.")
                continue
        question, responses, correct_response = await get_question_of_the_day(database_interface)
        if not question:
            log.info("No question of the day found to send.")
            return
        embed = discord.Embed(title="Question of the Day", description=question, color=discord.Color.blue())
        view = DayView(question_id=question, responses=responses, correct_response=correct_response)
        try:
            await channel.send(embed=embed, view=view)
            log.info(f"Sent question of the day to channel ID: {channel_id}")
        except Exception as e:
            log.error(f"Error sending question of the day to channel ID {channel_id}: {e}")
            return
        await asyncio.sleep(10)  # After predeterminate time send states and response
        correct_count, incorrect_count = view.count_responses()
        total_responses = correct_count + incorrect_count
        if total_responses == 0:
            await channel.send(f"No responses received for the question of the day. \n Correct response was: {correct_response['response_text']}")
            return
        await channel.send(f"Question of the Day has ended! \n Correct response was: {correct_response['response_text']} \n Total responses: {total_responses} \n Correct responses: {correct_count} \n Incorrect responses: {incorrect_count}")
        log.info(f"Correct responses: {correct_count}, Incorrect responses: {incorrect_count}")

    await planned_task(database_interface, bot, config)
    
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
        question = await database_interface.fetch_one("questions", ["id", "question_text"], "id = (SELECT id FROM questions ORDER BY id DESC LIMIT 1)")
        log.info(f"Fetched question of the day: {question}")
        if not question:
            return None, [], None
        question_id = dict(question)["id"]
        log.info(f"Question ID: {question_id}")
        question_text = dict(question)["question_text"]
    except Exception as e:
        log.error(f"Error fetching question of the day: {e}")
        return None, [], None

    try:
        responses = await database_interface.fetch_all("responses", ["id","response_text"], "question_id = $1", None, question_id)
        correct_response = await database_interface.fetch_one("responses", ["id", "response_text"], "question_id = $1 AND is_correct = TRUE", None, question_id)
        log.info(f"Fetched responses: {responses}")
        return question_text, [dict(response) for response in responses], dict(correct_response) if correct_response else None
    except Exception as e:
        log.error(f"Error fetching responses: {e}")
        return question_text, [], None

