import logging

import discord
from discord import app_commands

FEATURE = {
    "slug": "administration",
    "name": "Administration Feature",
    "description": "A feature that provides administration commands.",
    "version": "1.0.0",
    "author": "Tryno",
    "requires_config": True,
    "permissions": ["send_messages", "embed_links", "manage_messages", "kick_members", "ban_members"],
}


def register(tree: app_commands.CommandTree, config):
    group = app_commands.Group(name=FEATURE["slug"], description="Administration commands")

    @group.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="The reason for the ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.permissions_in(interaction.channel).ban_members:
            await interaction.response.send_message("❌ You don't have permission to ban members.", ephemeral=True)
            return

        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"✅ {member.mention} has been banned. Reason: {reason}")
            logging.getLogger(__name__).info(f"User {interaction.user} banned {member} for reason: {reason}")
        except discord.Forbidden:
            logging.getLogger(__name__).warning(f"Failed to ban {member} due to insufficient permissions.")
            await interaction.response.send_message("❌ I don't have permission to ban this member.", ephemeral=True)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error while trying to ban {member}: {e}")
            await interaction.response.send_message(
                f"❌ An error occurred while trying to ban the member: {e}", ephemeral=True
            )

    @group.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="The reason for the kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_member(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.permissions_in(interaction.channel).kick_members:
            await interaction.response.send_message("❌ You don't have permission to kick members.", ephemeral=True)
            logging.getLogger(__name__).warning(f"User {interaction.user} attempted to kick without permissions.")
            return

        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ {member.mention} has been kicked. Reason: {reason}")
            logging.getLogger(__name__).info(f"User {interaction.user} kicked {member} for reason: {reason}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this member.", ephemeral=True)
            logging.getLogger(__name__).warning(f"Failed to kick {member} due to insufficient permissions.")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error while trying to kick {member}: {e}")
            await interaction.response.send_message(
                f"❌ An error occurred while trying to kick the member: {e}", ephemeral=True
            )

    tree.add_command(group)
