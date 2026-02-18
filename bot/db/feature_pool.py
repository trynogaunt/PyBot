from typing import Optional

from .pool import DatabasePool


class FeaturePool(DatabasePool):
    def __init__(self, database_url: str = None, schemas: Optional[set[str]] = None):
        super().__init__(database_url=database_url, schemas=schemas)

    async def add_table(self, table_name: str, columns: str, schema: str = "features"):
        await self._create_table(schema, table_name, columns)
