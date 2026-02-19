import inspect
from typing import List, Optional

from .pool import DatabasePool


class FeaturePool(DatabasePool):
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        super().__init__(database_url=database_url, schemas=schemas)

    async def add_table(self, table_name: str, columns: List[str]):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS features.{table_name} (
                    {', '.join(columns)}
                );
            """
            )

    async def drop_table(self, table_name: str):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                    DROP TABLE IF EXISTS features.{table_name} CASCADE;
                """
            )

    def inspect_test(self):
        var_test = inspect.stack()
        return var_test
