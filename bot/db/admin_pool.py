from typing import Optional

from .pool import DatabasePool, List


class AdminPool(DatabasePool):
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        super().__init__(database_url=database_url, schemas=schemas)

    async def connect(self):
        await super().connect()
        await self.scheme_check()

    async def scheme_check(self):
        available_schemas = await self.get_available_schemas()
        missing_schemas = set(self.required_schemas) - set(available_schemas)
        if missing_schemas:
            for schema in missing_schemas:
                await self._create_schema(schema)

    async def _create_table(self, schema: str, table_name: str, columns: List[str]):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        available_schemas = await self.get_available_schemas()
        if schema not in available_schemas:
            raise ValueError(f"Schema must be one of {available_schemas}.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                    {', '.join(columns)}

                );
            """
            )

    async def _create_schema(self, schema: str):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        if not self._validate_schema(schema):
            raise ValueError(f"Schema must be one of {self.required_schemas}.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                CREATE SCHEMA IF NOT EXISTS {schema};
            """
            )

    async def _drop_schema(self, schema: str):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        if self._validate_schema(schema):
            raise ValueError(f"This schema is required and cannot be dropped: {schema}.")

        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                DROP SCHEMA IF EXISTS {schema} CASCADE;
            """
            )
