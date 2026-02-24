import inspect
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from .pool import DatabasePool


class FeaturePool(DatabasePool):
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        super().__init__(database_url=database_url, schemas=schemas)

    def _feature_schema(self) -> str:
        schema : str = str(self._get_feature_caller())
        return schema
    
    @asynccontextmanager
    async def _scoped_conn(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        schema = self._feature_schema()
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f"SET search_path TO {schema}")
                yield conn

    async def add_table(self, table_name: str, columns: List[str]):
        async with self._scoped_conn() as connection:
            await connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(columns)}
                );
            """)    

    async def drop_table(self, table_name: str):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            await connection.execute(
                f"""
                    DROP TABLE IF EXISTS {prefix}.{table_name} CASCADE;
                """
            )

    async def insert(self, table_name: str, columns: List[str], values: List):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(
                f"""
                INSERT INTO {prefix}.{table_name} ({', '.join(columns)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(values))])}) RETURNING id;
            """,
                *values,
            )
            return row["id"]

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
                DELETE FROM {prefix}.{table_name} WHERE {condition};
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
                UPDATE {prefix}.{table_name} SET {updates} WHERE {condition};
            """,
                *args,
            )

    async def count(self, table_name: str, condition: Optional[str] = None, *args) -> int:
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            query = f"SELECT COUNT(*) FROM {prefix}.{table_name}"
            if condition:
                query += f" WHERE {condition}"
            result = await connection.fetchval(query, *args)
            return result if result is not None else 0
        
    async def fetch_all(self, table_name: str, columns: List[str], condition: Optional[str] = None, *args):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            query = f"SELECT {', '.join(columns)} FROM {prefix}.{table_name}"
            if condition:
                query += f" WHERE {condition}"
            return await connection.fetch(query, *args)

    async def fetch_one(self, table_name: str, columns: List[str], condition: Optional[str] = None, order_by: Optional[str] = None, *args):
        prefix = str(self._get_feature_caller())
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        async with self.pool.acquire() as connection:
            query = f"SELECT {', '.join(columns)} FROM {prefix}.{table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            return await connection.fetchrow(query, *args)
        
    def _get_feature_caller(self):
        # Remonte la stack jusqu'à sortir du dossier 'db'
        stack = inspect.stack()
        for frame_info in stack:
            file_path = frame_info.filename
            parent_folder = Path(file_path).parent.name
            if parent_folder != "db":
                return parent_folder
        # Fallback si rien trouvé
        return "unknown"
