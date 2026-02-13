import discord
from discord import app_commands

FEATURE = {
    "slug": "utils",
    "name": "Utils Feature",
    "description": "A feature that provides help commands.",
    "version": "1.0.0",
    "author": "Tryno",
    "requires_config": True,
    "permissions": ["send_messages", "embed_links"],
}


def register(tree: app_commands.CommandTree, config):
    group = app_commands.Group(name=FEATURE["slug"], description="Help commands")

    @group.command(name="help", description="List all available commands")
    async def help_commands(interaction: discord.Interaction):
        commands_list = []
        discord_guild = (
            discord.utils.get(interaction.client.guilds, id=interaction.guild_id) if isinstance(config, dict) else None
        )
        if not discord_guild:
            await interaction.response.send_message(
                "❌ Impossible de récupérer les commandes pour ce serveur.", ephemeral=True
            )
            return
        for cmd in tree.get_commands(guild=discord_guild):
            if isinstance(cmd, app_commands.Group):
                for subcmd in cmd.commands:
                    commands_list.append(f"/{cmd.name} {subcmd.name} - {subcmd.description}")
            else:
                commands_list.append(f"/{cmd.name} - {cmd.description}")

        help_message = "Voici la liste des commandes disponibles :\n\n" + "\n".join(commands_list)
        await interaction.response.send_message(
            help_message, ephemeral=config.get("ephemeral_default", True) if isinstance(config, dict) else True
        )

    @group.command(name="serverinfo", description="Affiche les informations du serveur")
    async def server_info_command(interaction: discord.Interaction):
        guild = interaction.guild
        print(guild.owner if guild else "No guild found")
        if not guild:
            await interaction.response.send_message(
                "❌ Impossible de récupérer les informations du serveur.", ephemeral=True
            )
            return
        embed = discord.Embed(title=f"Informations sur {guild.name}", color=discord.Color.blue())
        embed.add_field(name="ID", value=guild.id, inline=False)
        embed.add_field(name="Propriétaire", value=guild.owner.name if guild.owner else "Inconnu", inline=False)
        embed.add_field(name="Membres", value=guild.member_count, inline=False)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        await interaction.response.send_message(
            embed=embed, ephemeral=config.get("ephemeral_default", True) if isinstance(config, dict) else True
        )

    tree.add_command(group)
