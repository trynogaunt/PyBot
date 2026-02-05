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
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this member.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                f"❌ An error occurred while trying to ban the member: {e}", ephemeral=True
            )

    tree.add_command(group)
