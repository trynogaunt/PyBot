import os
from typing import List, Optional

import asyncpg


class DatabasePool:
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        self.database_url = database_url
        self.required_schemas = schemas if schemas is not None else {"public"}
        self.pool: Optional[asyncpg.Pool] = None

    def _validate_schema(self, schema: str) -> bool:
        if schema not in self.required_schemas:
            return False
        return True

    async def connect(self):
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set.")
        self.pool = await asyncpg.create_pool(self.database_url)
        await self.scheme_check()

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

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

    async def get_available_schemas(self) -> list[str]:
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog');
                """
            )
            return [row["schema_name"] for row in rows]

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

    async def scheme_check(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")

        available_schemas = await self.get_available_schemas()
        missing_schemas = self.required_schemas - set(available_schemas)

        # add all schemas that are missing from env to the database
        if missing_schemas:
            for schema in missing_schemas:
                await self._create_schema(schema)

        available_schemas = await self.get_available_schemas()

        # drop all schemas that are not in env but are in the database
        for schema in available_schemas:
            if not self._validate_schema(schema):
                await self._drop_schema(schema)

    async def add_table(self, table_name: str, columns: str, schema: str = "features"):
        await self._create_table(schema, table_name, columns)
