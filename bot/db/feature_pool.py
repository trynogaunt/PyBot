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

    async def insert(self, table_name: str, columns: List[str], values: List):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                INSERT INTO features.{prefix}_{table_name} ({', '.join(columns)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(values))])});
            """,
                *values,
            )

    async def query(self, query: str, *args):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def delete(self, table_name: str, condition: str, *args):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                DELETE FROM features.{prefix}_{table_name} WHERE {condition};
            """,
                *args,
            )

    async def update(self, table_name: str, updates: str, condition: str, *args):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                UPDATE features.{prefix}_{table_name} SET {updates} WHERE {condition};
            """,
                *args,
            )

    def _get_feature_caller(self):
        file_caller = inspect.currentframe().f_back.f_globals["__file__"]
        parent_folder = Path(file_caller).parent.name
        return parent_folder
