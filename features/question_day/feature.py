import discord
from discord import app_commands

from bot.core.checks import is_staff
from bot.db.feature_pool import FeaturePool

# this feature is for testing purposes only, it will be used to test the feature system and the command system, it will not be used in production
# don't push on dev and main branches with this feature enabled, it can cause issues with the database and the bot, use it only on a testing branch and a testing server

FEATURE = {
    "slug": "question_day",  # The unique identifier for the feature
    "name": "Question of the Day",  # The display name of the feature
    "description": "A feature that allows the bot to manage the question of the day.",  # A brief description of the feature
    "version": "1.0.0",  # The version of the feature
    "author": "Tryno",  # The author of the feature
    "requires_config": False,  # Whether the feature requires configuration
    "permissions": ["send_messages", "embed_links"],  # Required permissions
}


def register(tree: app_commands.CommandTree, config):  # Register the feature's commands with the bot's command tree
    group = app_commands.Group(name=FEATURE["slug"], description="Testing commands")

    async def build_tables():


    @is_staff()
    @group.command(name="", description="Test command to check the parent folder of the command")
    async def ping_command(interaction: discord.Interaction):
        feature_pool = FeaturePool(
            database_url="postgresql://postgres:ifYRQjLcCffSACLmgHTVvhISeCrlNBtK@switchyard.proxy.rlwy.net:43556/railway",
            schemas={"features"},
        )

        parent_folder = feature_pool.inspect_test()
        await interaction.response.send_message(f"Parent folder: {parent_folder}", ephemeral=True)

    tree.add_command(group)
