import logging
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
    async def add_question_command(interaction: discord.Interaction, question: str):
        result = await add_question(database_interface, question)
        await interaction.response.send_message(result, ephemeral=True)

    tree.add_command(group)


async def install(database_interface: FeaturePool) -> bool:
    try:
        await database_interface.add_table("questions", ["id SERIAL PRIMARY KEY", "question_text TEXT"])
        await database_interface.add_table(
            "responses",
            [
                "id SERIAL PRIMARY KEY",
                "question_id INT REFERENCES questions(id)",
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
        await database_interface.insert("questions", ["question_text"], [question])
        question_id = await database_interface.fetch("questions", ["id"], "question_text = $1", [question])
        for response in responses:
            is_correct = response == correct_response
            await database_interface.insert(
                "responses", ["question_id", "response_text", "is_correct"], [question_id, response, is_correct]
            )
        return True
    except Exception as e:
        log.error(f"Error adding question: {e}")
        return False
