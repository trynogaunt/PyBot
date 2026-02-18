from __future__ import annotations

import logging
import os
import sys
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from ..core.checks import set_staff_roles
from ..core.config import load_config, load_env
from ..core.loader import load_features
from ..db.pool import DatabasePool


def setup_logging(level: str = "INFO") -> None:
    logs_dir = Path(__file__).resolve().parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    # Redirect stderr to stdout to fix Railway logging issues
    sys.stderr = sys.stdout

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    fh = RotatingFileHandler(
        logs_dir / f"bot_{date.today().isoformat()}.log",
        maxBytes=5_000_000,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)


class BotApp(commands.Bot):
    def __init__(self, guild_id: int) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild = discord.Object(id=guild_id)
        self.db_pool = None

    async def on_startup(self) -> None:
        logging.getLogger(__name__).info("Bot is starting up...")
        env = load_env()
        database_url = env.database_url
        print(f"Env: {env}")
        schemas = env.database_schemas if hasattr(env, "database_schemas") else None
        self.db_pool = DatabasePool(database_url=database_url, schemas=schemas)
        await self.db_pool.connect()

    async def on_shutdown(self) -> None:
        logging.getLogger(__name__).info("Bot is shutting down...")
        if self.db_pool:
            await self.db_pool.disconnect()

    async def setup_hook(self) -> None:
        await self.on_startup()
        self.tree.on_error = self.on_tree_error
        self.tree.clear_commands(guild=None)
        await self.tree.sync()

        loaded, failed = load_features(self.tree, self.config)
        logging.getLogger(__name__).info(f"Loaded features: {list(loaded.keys())}")
        if failed:
            logging.getLogger(__name__).warning(f"Failed to load features: {failed}")

        self.tree.copy_global_to(guild=self.guild)
        synced = await self.tree.sync(guild=self.guild)
        logging.getLogger(__name__).info("Synced %d commands to guild %s", len(synced), self.guild.id)

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:

        if isinstance(error, app_commands.CommandOnCooldown):
            logging.getLogger(__name__).warning(f"Command on cooldown {interaction.command}: {error}")
            await interaction.response.send_message(
                f"⏳ Cette commande est en cooldown. Réessaie dans {error.retry_after:.1f} secondes.",
                ephemeral=True,
            )
            return

        if isinstance(error, app_commands.MissingPermissions):
            logging.getLogger(__name__).warning(f"Missing permissions for command {interaction.command}: {error}")
            await interaction.response.send_message(
                "❌ Tu n'as pas les permissions nécessaires pour utiliser cette commande.", ephemeral=True
            )
            return

        if isinstance(error, app_commands.CheckFailure):
            logging.getLogger(__name__).warning(f"Check failed for command {interaction.command}: {error}")
            await interaction.response.send_message(
                "❌ Tu ne remplis pas les conditions pour utiliser cette commande.", ephemeral=True
            )
            return

        logging.getLogger(__name__).error(f"Error in command {interaction.command}: {error}")
        await interaction.response.send_message(
            "❌ Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True
        )

    async def on_disconnect(self) -> None:
        logging.getLogger(__name__).warning("Bot has been disconnected. Attempting to reconnect...")
        await self.on_shutdown()


def main() -> None:
    setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    load_dotenv()
    env = load_env()
    set_staff_roles(env.staff_roles_ids)

    config = load_config(env.config_path)

    bot = BotApp(guild_id=env.guild_id)
    bot.config = config

    bot.run(env.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
