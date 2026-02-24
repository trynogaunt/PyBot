import inspect
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager

from .pool import DatabasePool


class FeaturePool():
    def __init__(self, pool, schema: Optional[str] = None):
        self.schema = schema
        self.pool = pool

    def _feature_schema(self) -> str:
        if self.schema:
            return self.schema
    
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
    
    @asynccontextmanager
    async def _scoped_conn(self):
        if not self.pool:
            raise ValueError("Database pool is not initialized.")
        schema = self._feature_schema()
        print(f"Using schema '{schema}' for database operations.")
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(f"SET search_path TO {schema}")
                yield conn

    async def add_table(self, table_name: str, columns: List[str]):
        async with self._scoped_conn() as connection:
            print(f"Creating table '{table_name}' with columns {columns} in schema '{self._feature_schema()}'.")
            await connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {', '.join(columns)}
                );
            """)    

    async def drop_table(self, table_name: str):
        async with self._scoped_conn() as connection:
            await connection.execute(
                f"""
                    DROP TABLE IF EXISTS {table_name} CASCADE;
                """
            )   

    async def insert(self, table_name: str, columns: List[str], values: List):
        async with self._scoped_conn() as connection:
            try: 
                inserted_id = await connection.fetchrow(
                    f"""
                    INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['$' + str(i + 1) for i in range(len(values))])}) RETURNING id;
                """,
                    *values,
                )
                return inserted_id["id"] if inserted_id else None
            except Exception as e:
                log.error(f"Error executing insert: {e} \n Table: {table_name} \n Columns: {columns} \n Values: {values}")
                return None

    async def query(self, query: str, *args):
        async with self._scoped_conn() as connection:
            try: 
                await connection.fetch(query, *args)
                return True
            except Exception as e:
                log.error(f"Error executing query: {e} \n Query: {query} \n Args: {args}")
                return False

    async def delete(self, table_name: str, condition: str, *args):
        async with self._scoped_conn() as connection:
            try:
                await connection.execute(
                    f"""
                    DELETE FROM {table_name} WHERE {condition};
                """,
                    *args,
                )
                return True
            except Exception as e:
                log.error(f"Error executing delete: {e} \n Table: {table_name} \n Condition: {condition} \n Args: {args}")
                return False

    async def update(self, table_name: str, updates: str, condition: str, *args):
        async with self._scoped_conn() as connection:
            try:
                await connection.execute(
                    f"""
                    UPDATE {table_name} SET {updates} WHERE {condition};
                """,
                    *args,
                )
                return True
            except Exception as e:
                log.error(f"Error executing update: {e} \n Table: {table_name} \n Updates: {updates} \n Condition: {condition} \n Args: {args}")
                return False    

    async def count(self, table_name: str, condition: Optional[str] = None, *args) -> int:
        async with self._scoped_conn() as connection:
             query = f"SELECT COUNT(*) FROM {table_name}"
             if condition:
                 query += f" WHERE {condition}"
             result = await connection.fetchval(query, *args)
             return result if result is not None else 0
        
    async def fetch_all(self, table_name: str, columns: List[str], condition: Optional[str] = None, *args):
        async with self._scoped_conn() as connection:
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            return await connection.fetch(query, *args)

    async def fetch_one(self, table_name: str, columns: List[str], condition: Optional[str] = None, order_by: Optional[str] = None, *args):
        async with self._scoped_conn() as connection:
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            return await connection.fetchrow(query, *args)

    async def fetch_one(self, table_name: str, columns: List[str], condition: Optional[str] = None, order_by: Optional[str] = None, *args):
        async with self._scoped_conn() as connection:
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            if condition:
                query += f" WHERE {condition}"
            if order_by:
                query += f" ORDER BY {order_by}"
            return await connection.fetchrow(query, *args)
