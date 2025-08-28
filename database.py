import asyncpg
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def add_command(panel: str, sub_panel: str, command_name: str, description: str):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            """
            INSERT INTO commands(panel, sub_panel, command_name, description)
            VALUES($1, $2, $3, $4)
            """,
            panel, sub_panel, command_name, description
        )
    finally:
        await conn.close()

def get_panels(panel_type: str):
    if panel_type == "User Panel":
        return ["Anime Izlash", "Testlik", "Hamkorlik"]
    else:
        return ["Sozlamalar", "Postlar", "Statistika"]

def get_commands(panel: str):
    async def _get():
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            rows = await conn.fetch(
                "SELECT command_name, description FROM commands WHERE panel=$1", panel
            )
            return [{"command_name": r["command_name"], "description": r["description"]} for r in rows]
        finally:
            await conn.close()
    return asyncio.run(_get())

# ------------------ Baza keltir ------------------
async def create_tables():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS commands (
                id SERIAL PRIMARY KEY,
                panel VARCHAR(50) NOT NULL,
                sub_panel VARCHAR(50),
                command_name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )
    finally:
        await conn.close()

asyncio.run(create_tables())
