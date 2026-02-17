import os
from typing import Optional

import asyncpg


class DatabasePool:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.database_url:
            raise ValueError("DATABASE_URL is not set.")
        self.pool = await asyncpg.create_pool(self.database_url)

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
