from typing import Optional

from contextlib import asynccontextmanager
import asyncpg
from .pool import DatabasePool, List


class AdminPool():
    def __init__(self,pool: asyncpg.Pool):
        self.schema = "core"
        self.pool: Optional[asyncpg.Pool] = pool
        
    @asynccontextmanager
    async def _scoped_conn(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        schema = self.schema.replace('"', '""')

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f'SET LOCAL search_path TO "{schema}"')
                yield conn
    
    async def scheme_check(self):
        available_schemas = await self.get_available_schemas()
        missing_schemas = set(self.required_schemas) - set(available_schemas)
        if missing_schemas:
            for schema in missing_schemas:
                await self._create_schema(schema)

    async def check_core_tables(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS core.modules (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    installed BOOLEAN NOT NULL DEFAULT FALSE
                );
            """
            )

    async def get_installed_modules(self) -> List[str]:
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                SELECT name FROM core.modules WHERE installed = TRUE;
            """
            )
            print(f"Installed modules from database: {[row['name'] for row in rows]}")
            return [row["name"] for row in rows]

    async def set_module_installed(self, module_name: str, installed: bool = True):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            print(f"Setting module '{module_name}' installed status to {'installed' if installed else 'not installed'} in database.")
            await connection.execute(
                """
                INSERT INTO core.modules (name, installed) VALUES ($1, $2)
                ON CONFLICT (name) DO UPDATE SET installed = EXCLUDED.installed;
            """,
                module_name,
                installed,
            )

    async def _drop_features_tables(self, schema: str):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                DROP SCHEMA IF EXISTS {schema} CASCADE;
            """
            )
    
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
