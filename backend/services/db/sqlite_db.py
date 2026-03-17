import sqlite3
import datetime
from uuid import uuid4
import os
from core.config import settings

DB_PATH = "/data/placementbrain.db"


def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Chats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    
    # 2. Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        );
    """)
    
    # 3. Interviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            current_question TEXT NOT NULL,
            question_index INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()


def create_chat(chat_id: str = None, title: str = "New Chat") -> str:
    if not chat_id:
        chat_id = str(uuid4())
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chats (id, title, created_at) VALUES (?, ?, ?);",
        (chat_id, title, created_at)
    )
    conn.commit()
    conn.close()
    return chat_id


def get_chats() -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, created_at FROM chats ORDER BY created_at DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "created_at": r["created_at"]} for r in rows]


def delete_chat(chat_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM chats WHERE id = ?;", (chat_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_message(chat_id: str, role: str, content: str) -> str:
    msg_id = str(uuid4())
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if chat exists, if not create it dynamically (robust fallback)
    cursor.execute("SELECT id FROM chats WHERE id = ?;", (chat_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO chats (id, title, created_at) VALUES (?, ?, ?);",
            (chat_id, f"Chat session {chat_id[:8]}", created_at)
        )
    cursor.execute(
        "INSERT INTO messages (id, chat_id, role, content, created_at) VALUES (?, ?, ?, ?, ?);",
        (msg_id, chat_id, role, content, created_at)
    )
    conn.commit()
    conn.close()
    return msg_id


def get_messages(chat_id: str) -> list[dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at ASC;",
        (chat_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "created_at": r["created_at"]} for r in rows]


def create_interview(chat_id: str, topic: str, current_question: str) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Cancel any previous active interviews for this chat first
    cursor.execute(
        "UPDATE interviews SET status = 'completed' WHERE chat_id = ? AND status = 'active';",
        (chat_id,)
    )
    int_id = str(uuid4())
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cursor.execute(
        "INSERT INTO interviews (id, chat_id, topic, current_question, question_index, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
        (int_id, chat_id, topic, current_question, 1, "active", created_at)
    )
    conn.commit()
    conn.close()
    return int_id


def get_active_interview(chat_id: str) -> dict | None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, topic, current_question, question_index, status FROM interviews WHERE chat_id = ? AND status = 'active';",
        (chat_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row["id"],
            "topic": row["topic"],
            "current_question": row["current_question"],
            "question_index": row["question_index"],
            "status": row["status"],
        }
    return None


def update_interview(interview_id: str, next_question: str, question_index: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE interviews SET current_question = ?, question_index = ?, status = ? WHERE id = ?;",
        (next_question, question_index, status, interview_id)
    )
    conn.commit()
    conn.close()
