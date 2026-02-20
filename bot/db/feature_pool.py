import inspect
from pathlib import Path
from typing import List, Optional

from .pool import DatabasePool


class FeaturePool(DatabasePool):
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        super().__init__(database_url=database_url, schemas=schemas)

    async def add_table(self, table_name: str, columns: List[str]):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS features.{prefix}_{table_name} (
                    {', '.join(columns)}
                );
            """
            )

    async def drop_table(self, table_name: str):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                    DROP TABLE IF EXISTS features.{prefix}_{table_name} CASCADE;
                """
            )

    def _get_feature_caller(self):
        file_caller = inspect.currentframe().f_back.f_globals["__file__"]
        parent_folder = Path(file_caller).parent.name
        return parent_folder
