import datetime

import discord
from discord import app_commands

from bot.core.checks import is_staff

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
        if not guild:
            await interaction.response.send_message(
                "❌ Impossible de récupérer les informations du serveur.", ephemeral=True
            )
            return
        embed = discord.Embed(title=f"Informations sur {guild.name}", color=discord.Color.blue())
        embed.set_image(url=guild.banner.url if guild.banner else None)
        embed.add_field(name="Date de création", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="ID", value=guild.id, inline=False)
        if guild.owner:
            embed.add_field(name="Propriétaire", value=guild.owner.name if guild.owner else "Inconnu", inline=False)
        embed.add_field(name="Membres", value=guild.member_count, inline=True)
        embed.add_field(name="Rôles", value=len(guild.roles), inline=True)
        embed.add_field(name="Salons", value=len(guild.channels), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boosts", value=f"{guild.premium_subscription_count}", inline=True)
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(
            text="PyBot - Utils Feature",
            icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None,
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=config.get("ephemeral_default", True) if isinstance(config, dict) else True
        )

    @group.command(name="remind", description="Créer un rappel")
    async def remind(interaction: discord.Interaction, count: int, unit: str, *, message: str):
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        if unit not in time_units:
            await interaction.response.send_message(
                "❌ Unité de temps invalide. Utilisez 's' pour secondes, 'm' pour minutes, 'h' pour heures ou 'd' pour jours.",
                ephemeral=True,
            )
            return
        delay = count * time_units[unit]
        await interaction.response.send_message(
            f"⏰ Rappel créé ! Je vous rappellerai dans {count} {unit}.", ephemeral=True
        )
        await discord.utils.sleep_until(discord.utils.utcnow() + datetime.timedelta(seconds=delay))
        await interaction.user.send(f"⏰ Rappel : {message}")

    @group.command(name="ping", description="Affiche la latence du bot")
    async def ping(interaction: discord.Interaction):
        latency = interaction.client.latency * 1000  # Convertir en millisecondes
        await interaction.response.send_message(f"🏓 Pong ! Latence : {latency:.2f} ms", ephemeral=True)

    @group.command(name="uptime", description="Affiche le temps de fonctionnement du bot")
    async def uptime(interaction: discord.Interaction):
        if not hasattr(interaction.client, "start_time"):
            await interaction.response.send_message(
                "❌ Impossible de récupérer le temps de fonctionnement.", ephemeral=True
            )
            return
        uptime_seconds = (discord.utils.utcnow() - interaction.client.start_time).total_seconds()
        uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
        await interaction.response.send_message(f"⏱️ Temps de fonctionnement : {uptime_str}", ephemeral=True)

    @group.command(name="invite", description="Affiche le lien d'invitation du bot")
    async def invite(interaction: discord.Interaction):
        invite_link = f"https://discord.com/api/oauth2/authorize?client_id={interaction.client.user.id}&permissions=8&scope=bot%20applications.commands"
        await interaction.response.send_message(f"🔗 Voici le lien d'invitation du bot : {invite_link}", ephemeral=True)

    @group.command(name="embed_message", description="Affiche un message dans un embed")
    @app_commands.describe(
        title="Le titre de l'embed",
        description="La description de l'embed",
        color="La couleur de l'embed (blue, red, green, yellow, purple, orange)",
    )
    @is_staff()
    async def embed_message(interaction: discord.Interaction, title: str, description: str, color: str = "blue"):
        if color.lower() not in ["blue", "red", "green", "yellow", "purple", "orange"]:
            await interaction.response.send_message(
                "❌ Couleur invalide. Utilisez 'blue', 'red', 'green', 'yellow', 'purple' ou 'orange'.", ephemeral=True
            )
            return
        color_mapping = {
            "blue": discord.Color.blue(),
            "red": discord.Color.red(),
            "green": discord.Color.green(),
            "yellow": discord.Color.gold(),
            "purple": discord.Color.purple(),
            "orange": discord.Color.orange(),
        }
        embed = discord.Embed(
            title=title, description=description, color=color_mapping.get(color.lower(), discord.Color.blue())
        )
        await interaction.response.send_message(
            embed=embed, ephemeral=config.get("ephemeral_default", True) if isinstance(config, dict) else True
        )

    @group.command(name="botinfo", description="Affiche les informations du bot")
    async def botinfo(interaction: discord.Interaction):
        info_str = f"**Nom du bot :** {interaction.client.user.name}\n"
        info_str += f"**ID du bot :** {interaction.client.user.id}\n"
        info_str += f"**Serveurs :** {len(interaction.client.guilds)}\n"
        info_str += f"**Utilisateurs :** {len(interaction.client.users)}\n"
        info_str += f"**Latence :** {interaction.client.latency * 1000:.2f} ms\n"
        await interaction.response.send_message(
            info_str, ephemeral=config.get("ephemeral_default", True) if isinstance(config, dict) else True
        )

    tree.add_command(group)
