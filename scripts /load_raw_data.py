import json
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()


# -----------------------------------------------------------------------------
# 1. Database connection setup
# -----------------------------------------------------------------------------
def get_db_connection() -> Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    """
    Establish a connection to the PostgreSQL database using environment variables.

    Returns:
        Tuple containing the database connection and cursor.

    Raises:
        Exception: If connection fails, prints error and exits the script.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            host=os.getenv("DATABASE_HOST"),
            port=os.getenv("DATABASE_PORT")
        )
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        exit()


conn, cur = get_db_connection()


# -----------------------------------------------------------------------------
# 2. Ensure schema and table exist
# -----------------------------------------------------------------------------
def ensure_schema_and_table(cursor: psycopg2.extensions.cursor) -> None:
    """
    Ensure that the schema 'raw' and the table 'telegram_messages' exist in the database.

    Args:
        cursor: Database cursor.
    """
    cursor.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;

    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
        message_id BIGINT PRIMARY KEY,
        channel_name TEXT,
        channel_title TEXT,
        message_date TIMESTAMP,
        message_text TEXT,
        has_media BOOLEAN,
        image_path TEXT,
        views INT,
        forwards INT
    );
    """)
    conn.commit()


ensure_schema_and_table(cur)


# -----------------------------------------------------------------------------
# 3. Load JSON files and insert into database
# -----------------------------------------------------------------------------
def load_json_files_to_db(data_path: Path, cursor: psycopg2.extensions.cursor) -> None:
    """
    Load Telegram message JSON files from a directory and insert the messages into PostgreSQL.

    Args:
        data_path: Path to the directory containing JSON files.
        cursor: Database cursor.
    """
    json_files: List[Path] = list(data_path.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {data_path}")
        return

    for file in json_files:
        with open(file, "r", encoding="utf-8") as f:
            try:
                messages: Any = json.load(f)
                # Ensure the JSON is a list
                if not isinstance(messages, list):
                    print(f"⚠️ {file.name} is not a list. Skipping.")
                    continue
            except json.JSONDecodeError as e:
                print(f"⚠️ Failed to read {file}: {e}")
                continue

            records: List[Tuple[Any, ...]] = []
            for msg in messages:
                # CRITICAL FIX: Verify msg is a dictionary
                if not isinstance(msg, dict):
                    print(f"⚠️ Skipping item because it is {type(msg)} instead of dict: {msg}")
                    continue

                try:
                    records.append((
                        msg.get("message_id"),
                        msg.get("channel_name"),
                        msg.get("channel_title"),
                        datetime.fromisoformat(msg.get("message_date").replace('Z', '+00:00')) if msg.get("message_date") else None,
                        msg.get("message_text"),
                        msg.get("has_media", False),
                        msg.get("image_path"),
                        msg.get("views", 0) if msg.get("views") is not None else 0,
                        msg.get("forwards", 0) if msg.get("forwards") is not None else 0
                    ))
                except Exception as e:
                    print(f"⚠️ Error processing a message in {file.name}: {e}")
                    continue

            if records:
                execute_values(
                    cursor,
                    """
                    INSERT INTO raw.telegram_messages 
                    (message_id, channel_name, channel_title, message_date, message_text, 
                     has_media, image_path, views, forwards)
                    VALUES %s
                    ON CONFLICT (message_id) DO NOTHING
                    """,
                    records
                )
                print(f"✅ Loaded {len(records)} messages from {file.name}")


data_path: Path = Path(__file__).resolve().parent.parent / "data" / "raw" / "telegram_messages" / "2026-01-18"
load_json_files_to_db(data_path, cur)


# -----------------------------------------------------------------------------
# 4. Cleanup
# -----------------------------------------------------------------------------
def cleanup(conn: psycopg2.extensions.connection, cursor: psycopg2.extensions.cursor) -> None:
    """
    Commit the database transaction and close the cursor and connection.

    Args:
        conn: Database connection.
        cursor: Database cursor.
    """
    conn.commit()
    cursor.close()
    conn.close()
    print("🎉 All raw data loaded into PostgreSQL successfully!")


cleanup(conn, cur)
