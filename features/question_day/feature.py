import discord
from discord import app_commands

from bot.core.checks import is_staff
from bot.db.feature_pool import FeaturePool

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


async def init_db(database_interface: FeaturePool):
    print("Initializing database tables for Question of the Day feature...")
    try:
        await database_interface.add_table("questions", ["id SERIAL PRIMARY KEY", "question_text TEXT"])
        return "Tables created successfully."
    except Exception as e:
        print(f"Error initializing database tables: {e}")


async def add_question(database_interface: FeaturePool, question: str):
    try:
        await database_interface.insert("questions", ["question_text"], [question])
        return "Question added successfully."
    except Exception as e:
        print(f"Error adding question: {e}")
