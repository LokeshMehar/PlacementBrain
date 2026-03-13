import asyncio
import json
import logging
from typing import AsyncGenerator

import redis
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_classic.callbacks import AsyncIteratorCallbackHandler
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)


class PlacementAgent:
    """ReAct agent with conversational memory and session persistence."""

    def __init__(self, llm, tools: list, redis_client: redis.Redis):
        self.llm = llm
        self.tools = tools
        self.redis_client = redis_client
        self.memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True,
        )
        self._last_sources: list[dict] = []

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are Antigravity, a helpful assistant for campus placements. You have access to tools to search the knowledge base, compare resumes against JDs, explain code, and generate quizzes. Use these tools ONLY when needed to answer queries requiring structured database searches, code explanations, or quizzes. If asked general questions, greetings, or conversational follow-up (e.g., 'hello', 'tell me a joke', 'what is the capital of India?'), DO NOT call any tools and answer directly using your knowledge. Be concise but thorough."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Initialize the agent
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
        )

    def _load_session_memory(self, session_id: str) -> None:
        """Load chat history from SQLite for session persistence."""
        try:
            from services.db import sqlite_db
            messages = sqlite_db.get_messages(session_id)
            self.memory.clear()
            for msg in messages:
                if msg["role"] == "human":
                    self.memory.chat_memory.add_message(
                        HumanMessage(content=msg["content"])
                    )
                elif msg["role"] == "ai":
                    self.memory.chat_memory.add_message(
                        AIMessage(content=msg["content"])
                    )
        except Exception as e:
            logger.warning(f"Failed to load session memory: {e}")

    def _save_session_memory(self, session_id: str) -> None:
        """Save chat memory - handled inline by chat router in SQLite."""
        pass

    async def astream(
        self, message: str, session_id: str
    ) -> AsyncGenerator[str, None]:
        """Stream agent response tokens asynchronously."""
        self._load_session_memory(session_id)
        
        from services.agent.tools import active_sources
        sources_list = []
        token_ctx = active_sources.set(sources_list)
        self._last_sources = sources_list

        try:
            callback = AsyncIteratorCallbackHandler()

            # Run the agent in a separate task
            task = asyncio.create_task(
                self.agent.ainvoke(
                    {"input": message},
                    config={"callbacks": [callback]},
                )
            )

            full_response = ""

            try:
                # Safely consume from the callback queue while the task is running
                while not task.done():
                    try:
                        # Wait for a token with a short timeout
                        token = await asyncio.wait_for(callback.queue.get(), timeout=0.1)
                        if token:
                            full_response += token
                            yield token
                    except asyncio.TimeoutError:
                        continue

                # Drain any remaining tokens
                while not callback.queue.empty():
                    try:
                        token = callback.queue.get_nowait()
                        if token:
                            full_response += token
                            yield token
                    except asyncio.QueueEmpty:
                        break
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"\n\n[Error: {str(e)}]"

            # Wait for the task to complete
            try:
                result = await task
                # Extract any tool usage info for sources
                if isinstance(result, dict) and "output" in result:
                    # If the full response is empty, use the output
                    if not full_response:
                        full_response = result["output"]
                        yield full_response
            except Exception as e:
                logger.error(f"Agent task error: {e}", exc_info=True)
                yield f"\n\n[Agent Error: {str(e)}]"

            self._save_session_memory(session_id)

            # Yield sources marker
            sources_json = json.dumps(self._last_sources)
            yield f"__SOURCES__{sources_json}"
        finally:
            active_sources.reset(token_ctx)

    def get_last_sources(self) -> list[dict]:
        """Return sources from the last agent run."""
        return self._last_sources
