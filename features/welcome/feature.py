import discord
from discord import app_commands
from discord.ext import commands

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
    group = app_commands.Group(name=FEATURE["slug"], description="Welcome commands")

    @commands.Cog.listener()
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

        channel = interaction.guild.system_channel if interaction.guild else None

        if welcome_message:
            embed = discord.Embed(title="Welcome!", description=welcome_message, color=discord.Color.green())
            (
                await channel.send(embed=embed)
                if channel
                else await interaction.response.send_message(welcome_message, ephemeral=True)
            )
        else:
            await interaction.response.send_message("Welcome to the server!", ephemeral=True)

    @group.command(name="welcome", description="Get the bot version")
    async def welcome_command(interaction: discord.Interaction):
        """
        Provide a welcome message to the user.
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
        channel = interaction.guild.system_channel if interaction.guild else None
        if welcome_message:
            embed = discord.Embed(title="Welcome!", description=welcome_message, color=discord.Color.green())
            (
                await channel.send(embed=embed)
                if channel
                else await interaction.response.send_message(
                    welcome_message, ephemeral=config.get("ephemeral_default", True)
                )
            )
        else:
            await interaction.response.send_message("Welcome to the server!", ephemeral=True)

    @group.command(name="version", description="Get the bot version")
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
