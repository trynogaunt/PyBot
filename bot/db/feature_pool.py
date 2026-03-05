import inspect
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
import asyncpg
import logging

log = logging.getLogger(__name__)

class FeaturePool():
    def __init__(self, pool:asyncpg.Pool, schema: Optional[str] = None):
        self.schema = schema if schema else "public"
        self.pool = pool
    
    
    @asynccontextmanager
    async def _scoped_conn(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        schema = self.schema.replace('"', '""')

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f'SET LOCAL search_path TO "{schema}"')
                yield conn

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        async with self._scoped_conn() as conn:
            return await conn.fetch(query, *args)
    
    async def execute(self, query: str, *args) -> str:
        async with self._scoped_conn() as conn:
            return await conn.execute(query, *args)

    async def add_table(self, table_name: str, columns: List[str]) -> bool:
        try:
            columns_sql = ", ".join(columns)
            await self.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY, {columns_sql})")
            return True
        except Exception as e:
            log.error(f"Error creating table {table_name}: {e}")
            return False
    
    async def drop_table(self, table_name: str) -> bool:
        try:
            await self.execute(f"DROP TABLE IF EXISTS {table_name}")
            return True
        except Exception as e:
            log.error(f"Error dropping table {table_name}: {e}")
            return False
    
    async def count(self, table_name: str, condition: Optional[str] = None) -> int:
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            result = await self.fetch(query)
            return result[0][0] if result else 0
        except Exception as e:
            log.error(f"Error counting rows in {table_name}: {e}")
            return 0
    
    async def fetch_one(self, table_name: str, columns: List[str], condition: Optional[str] = None, order_by: Optional[str] = None, *args) -> Optional[asyncpg.Record]:
        try:
            columns_sql = ", ".join(columns)
            query = f"SELECT {columns_sql} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            result = await self.fetch(query, *args)
            return result[0] if result else None
        except Exception as e:
            log.error(f"Error fetching from {table_name}: {e}")
            return None
    
    async def fetch_all(self, table_name: str, columns: List[str], condition: Optional[str] = None, order_by: Optional[str] = None, *args) -> List[asyncpg.Record]:
        try:
            columns_sql = ", ".join(columns)
            query = f"SELECT {columns_sql} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            log.info(f"Executing query: {query} with args: {args}")
            return await self.fetch(query, *args)
        except Exception as e:
            log.error(f"Error fetching from {table_name}: {e}")
            return []
    
    async def insert(self, table_name: str, columns: List[str], values: List) -> int:
        try:
            columns_sql = ", ".join(columns)
            placeholders = ", ".join(f"${i+1}" for i in range(len(values)))
            query = f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholders}) RETURNING id"
            log.info(f"Executing query: {query} with values: {values}")
            result = await self.query(query, *values)
            return result[0]["id"] if result else None
        except Exception as e:
            log.error(f"Error inserting into {table_name}: {e}")
            return None
    
    async def query(self, query: str, *args) -> List[asyncpg.Record]:
        try:
            async with self._scoped_conn() as conn:
                return await conn.fetch(query, *args)
        except Exception as e:
            log.error(f"Error executing query: {e}")
            return []