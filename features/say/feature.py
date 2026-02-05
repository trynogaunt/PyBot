import discord
from discord import app_commands

FEATURE = {
    "slug": "say",  # The unique identifier for the feature
    "name": "Say Feature",  # The display name of the feature
    "description": "A feature that allows the bot to say messages.",  # A brief description of the feature
    "version": "1.0.0",  # The version of the feature
    "author": "Tryno",  # The author of the feature
    "requires_config": True,  # Whether the feature requires configuration
    "permissions": ["send_messages", "embed_links"],  # Required permissions
}


def register(tree: app_commands.CommandTree, config):  # Register the feature's commands with the bot's command tree
    @tree.command(name=FEATURE["slug"], description=FEATURE["description"])  # Define a new command in the command tree
    @app_commands.describe(message="The message for the bot to say.")  # Describe the command parameter
    async def say_command(
        interaction: discord.Interaction, message: str
    ):  # The command function that will be called when the command is invoked
        """
        Make the bot say a message.
        Arguments:
            interaction: The interaction object.
            message: The message to be sent by the bot.
        """
        ephemeral_default = (
            bool(config.get("ephemeral_default")) if isinstance(config, dict) else False
        )  # Get ephemeral default from config
        await interaction.response.send_message(
            message, ephemeral=ephemeral_default
        )  # Respond with the provided message
        # Add any additional logic for your custom feature here
