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

_AVAILABLE_QUESTION = "asked_at IS NULL OR asked_at < NOW() - INTERVAL '30 day'"


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

    @group.command(name="question", description="Get the current question of the day")
    @is_staff()
    async def get_question_command(interaction: discord.Interaction):
       question = await get_question_of_the_day(database_interface)
       print(f"Question of the day: {question}")
       if question:
            await interaction.response.send_message(f"Current question of the day: {question[0]}", ephemeral=True)
       else:
            await interaction.response.send_message("No question of the day found.", ephemeral=True) 

            
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
                "asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
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

async def get_question_of_the_day(database_interface: FeaturePool) -> Tuple[str, List[Dict[str, str]], Dict[str, str]]:
    """
    Fetches the question of the day and its responses from the database.
    Returns a tuple containing the question text, a list of responses, and the correct response.
    """
    try:
        questions = await database_interface.fetch_all("questions", ["id", "question_text"], _AVAILABLE_QUESTION)
        log.info(f"Fetched questions: {questions}")
    except Exception as e:
        log.error(f"Error fetching question of the day: {e}")
        return None, [], None

    if not questions:
        log.info("No available questions found.")
        return None, [], None

