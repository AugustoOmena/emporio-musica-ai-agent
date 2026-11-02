import glob
from pathlib import Path
from typing import List, Dict, Any
import duckdb

from src.utils import sanitize_identifier


class DatabaseManager:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.conn = duckdb.connect(database=":memory:")
        self._load_csv_tables()

    def _load_csv_tables(self) -> None:
        csv_files = glob.glob(str(self.data_dir / "*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No .csv files found in '{self.data_dir}'.")

        for file_path in csv_files:
            table_name = sanitize_identifier(Path(file_path).stem)
            escaped_path = file_path.replace("'", "''")
            query = f"""
                CREATE OR REPLACE TABLE "{table_name}" AS 
                SELECT * FROM read_csv_auto('{escaped_path}');
            """
            self.conn.execute(query)

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"]
        if any(clean_query.upper().startswith(kw) for kw in forbidden_keywords):
            raise ValueError("Mutation operations are not allowed.")

        cursor = self.conn.execute(clean_query)
        if not cursor.description:
            return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_table_schema(self) -> str:
        tables = self.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main';"
        ).fetchall()

        schema_details = []
        for (table_name,) in tables:
            columns = self.conn.execute(
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}';"
            ).fetchall()
            cols_format = ", ".join([f"{col} ({dtype})" for col, dtype in columns])
            schema_details.append(f"Table '{table_name}': [{cols_format}]")

        return "\n".join(schema_details)


db_manager = DatabaseManager()