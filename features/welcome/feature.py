import discord
from discord import app_commands

FEATURE = {
    "slug": "welcome",
    "name": "Welcome Feature",
    "description": "A feature that provides welcome messages and onboarding for new members.",
    "version": "1.0.0",
    "author": "Tryno",
    "requires_config": True,
    "permissions": ["send_messages", "embed_links"],
}


def register(tree: app_commands.CommandTree, config):
    async def on_member_join(interaction: discord.Interaction):
        """
        Send a welcome message to new members.
        Arguments:
            interaction: The interaction object.
        """
        welcome_message = (
            config.get("welcome_message", "").format(
                member=interaction.user.mention, guild=interaction.guild.name if interaction.guild else "ce serveur"
            )
            if isinstance(config, dict)
            else None
        )
        if welcome_message:
            embed = discord.Embed(title="Welcome!", description=welcome_message, color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Welcome to the server!", ephemeral=True)

    tree.add_listener(on_member_join, "on_member_join")

    @tree.command(name=FEATURE["slug"], description=FEATURE["description"])
    async def version_command(interaction: discord.Interaction):
        """
        Provide the bot's version information.
        Arguments:
            interaction: The interaction object.
        """
        bot_version = FEATURE["version"]
        embed = discord.Embed(
            title="Bot Version", description=f"The current bot version is {bot_version}.", color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
