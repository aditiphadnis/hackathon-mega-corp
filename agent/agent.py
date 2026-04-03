import asyncio
import uuid
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from .bq_agent import bq_agent

# Required by adk web
root_agent = bq_agent



session_service = InMemorySessionService()
runner = Runner(
    agent=bq_agent,
    app_name="bq_agent",
    session_service=session_service,
)

APP_NAME   = "agent"
USER_ID    = str(uuid.uuid4())
SESSION_ID = str(uuid.uuid4())

async def init_session():
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

async def chat(user_message: str):
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_message)]
    )
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if hasattr(p, "text"))
                print(f"\nAgent: {text}\n")

async def main():
    await init_session()
    print(f"BigQuery Agent ready (session: {SESSION_ID[:8]}...)\n")
    print("Ask questions about your data (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break
        await chat(user_input)

if __name__ == "__main__":
    asyncio.run(main())
