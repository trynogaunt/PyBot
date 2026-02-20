from discord import app_commands

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
    tree.add_command(group)


async def init_db(database_interface: FeaturePool):
    print("Initializing database tables for Question of the Day feature...")
    try:
        await database_interface.add_table("test_table", ["id SERIAL PRIMARY KEY", "name TEXT"])
        return "Tables created successfully."
    except Exception as e:
        print(f"Error initializing database tables: {e}")
