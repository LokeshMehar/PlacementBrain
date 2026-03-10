import asyncio
import json

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from core.dependencies import get_agent, get_semantic_cache
from services.db import sqlite_db

router = APIRouter()


class ChatCreate(BaseModel):
    title: str = "New Chat"


class ChatResponse(BaseModel):
    id: str
    title: str
    created_at: str


@router.post("", response_model=ChatResponse)
async def create_new_chat(body: ChatCreate = None):
    title = body.title if body else "New Chat"
    chat_id = sqlite_db.create_chat(title=title)
    chats = sqlite_db.get_chats()
    for c in chats:
        if c["id"] == chat_id:
            return c
    raise HTTPException(status_code=500, detail="Failed to create chat")


@router.get("", response_model=list[ChatResponse])
async def list_chats():
    return sqlite_db.get_chats()


@router.delete("/{chat_id}")
async def delete_chat_session(chat_id: str):
    deleted = sqlite_db.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "success"}


@router.get("/{chat_id}/messages")
async def get_chat_messages(chat_id: str):
    return sqlite_db.get_messages(chat_id)


@router.get("/stream")
async def chat_stream(
    message: str = Query(..., description="User message"),
    session_id: str = Query(..., description="Session ID"),
    source_type_filter: str = Query(None, description="Comma-separated source types"),
    cache=Depends(get_semantic_cache),
    agent=Depends(get_agent),
):
    """Stream chat response using Server-Sent Events."""

    # Save human message to database immediately
    sqlite_db.add_message(session_id, "human", message)

    async def event_generator():
        # Check semantic cache first (scoped by session_id/chat_id)
        cached_response = cache.get(session_id, message)

        if cached_response:
            # Stream cached response character by character
            for char in cached_response:
                event_data = json.dumps({"type": "token", "data": char})
                yield {"data": event_data}
                await asyncio.sleep(0.01)  # 10ms delay

            # Save cached AI response to database
            sqlite_db.add_message(session_id, "ai", cached_response)

            # Send done event
            done_data = json.dumps({"type": "done", "sources": []})
            yield {"data": done_data}
            return

        # Cache miss — stream from agent
        full_response = ""
        sources = []

        async for token in agent.astream(message, session_id):
            # Check for sources marker
            if token.startswith("__SOURCES__"):
                try:
                    sources_json = token[len("__SOURCES__"):]
                    sources = json.loads(sources_json)
                except json.JSONDecodeError:
                    sources = []
                continue

            full_response += token
            event_data = json.dumps({"type": "token", "data": token})
            yield {"data": event_data}

        # Cache the full response (scoped by session_id)
        if full_response.strip():
            cache.set(session_id, message, full_response)
            # Save actual AI response to database
            sqlite_db.add_message(session_id, "ai", full_response)

        # Send done event with sources
        done_data = json.dumps({"type": "done", "sources": sources})
        yield {"data": done_data}

    return EventSourceResponse(event_generator())
