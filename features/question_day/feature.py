import logging
import datetime
import time
import random
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

    @group.command(name="send", description="Send the question of the day to a channel")
    @is_staff()
    async def send_question_command(interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        await send_question_of_the_day(bot, database_interface, channel.id)
        await interaction.followup.send(f"Sent question of the day to {channel.mention}", ephemeral=True)
            
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
    except Exception as e:
        log.error(f"Error fetching question of the day: {e}")
        return None, [], None

    if not questions:
        log.info("No available questions found.")
        return None, [], None
    
    log.info(f"Fetched questions: {questions}")
    selected_question = random.choice(questions)
    question_id = selected_question["id"]
    question_text = selected_question["question_text"]
    log.info(f"Selected question ID: {question_id}, text: {question_text}")
    try:
        responses = await database_interface.fetch_all("responses", ["response_text", "is_correct"], f"question_id = {question_id}")
    except Exception as e:
        log.error(f"Error fetching responses for question ID {question_id}: {e}")
        return question_text, [], None
    
    log.info(f"Fetched responses for question ID {question_id}: {responses}")
    correct_response = next((r for r in responses if r["is_correct"]), None)
    return question_text, responses, correct_response

async def mark_question_as_asked(database_interface: FeaturePool, question_id: int) -> bool:
    """
    Marks the specified question as asked by updating the asked_at timestamp.
    """
    try:
        await database_interface.execute(f"UPDATE responses SET asked_at = NOW() WHERE question_id = {question_id}")
        return True
    except Exception as e:
        log.error(f"Error marking question ID {question_id} as asked: {e}")
        return False
    
async def send_question_of_the_day(bot: discord.Client, database_interface: FeaturePool, channel_id: int):
    question_text, responses, correct_response = await get_question_of_the_day(database_interface)
    if not question_text:
        log.info("No question of the day to send.")
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        log.error(f"Channel with ID {channel_id} not found.")
        return
    
    view = DayView(question_text,responses, correct_response)
    
    try:
        await channel.send(content=f"**Question of the Day:** {question_text}", view=view)
        log.info(f"Sent question of the day to channel ID {channel_id}")
    except Exception as e:
        log.error(f"Error sending question of the day: {e}")
