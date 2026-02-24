import os
from typing import List, Optional



class DatabasePool:
    def __init__(self, database_url: str = None):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    def _ensure_connected(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized. Call connect() first.")
    
    def for_schema(self, schema: str):
        self._ensure_connected()
        from .feature_pool import FeaturePool
        return FeaturePool(self.pool, schema=schema)
    
    def _validate_schema(self, schema: str) -> bool:
        if schema not in self.required_schemas:
            return False
        return True

    async def connect(self):
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set.")
        self.pool = await asyncpg.create_pool(self.database_url, min_size=1, max_size=10)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def get_available_schemas(self) -> list[str]:
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(
                """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast');
                """
            )
            return [row["schema_name"] for row in rows]
