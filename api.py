# To run this api uvicorn api:app --reload 
# import os # Unused
# import time # Unused
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Import your agent and tools (once)
from agent import root_agent
from tools import store_chat_message
from google.adk.runners import Runner # InvocationContext, Session are likely used by Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # CHANGE THIS FOR PRODUCTION!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="ocat_chatbot",
    session_service=session_service
)

class ChatMessage(BaseModel):
    sender: str
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_request: ChatRequest):
    user_message_content = chat_request.message
    session_id = chat_request.session_id
    user_id = "anonymous_user"  # You might want to pass this from the frontend

    # --- 1. Create session ---
    session = session_service.create_session(  
        app_name=runner.app_name,
        user_id=user_id,
        session_id=session_id
    )
    
    if not session:
        raise HTTPException(status_code=500, detail="Session could not be established.")

    # --- 2. Store User Message ---
    user_message_to_store = f"User: {user_message_content}"
    print(f"Attempting to store user message: {user_message_to_store[:100]}...")
    store_user_msg_result = store_chat_message(user_message_to_store)
    if isinstance(store_user_msg_result, dict) and "error" in store_user_msg_result:
        print(f"Failed to store user message in DB: {store_user_msg_result['error']}")
        # Decide if you want to raise an HTTPException here or just log

    final_agent_response = ""
    # --- 3. Run the Agent and Process Events ---
    try:
        # Create message using proper types from google.genai
        content = types.Content(
            role='user',
            parts=[types.Part(text=user_message_content)]
        )

        print(f"Sending message to agent: {user_message_content}")  # Debug print

        max_retries = 3
        retry_count = 0
        retry_delay = 1  # Start with 1 second delay
        
        while retry_count < max_retries:
            try:
                async for event in runner.run_async(
                    session_id=session_id,
                    user_id=user_id,
                    new_message=content
                ):
                    print(f"Received event: {event}")  # Debug print
                    # print(f"Event type: {getattr(event, 'event_type', None)}") # Kept for debugging if needed
                    # print(f"Event content: {getattr(event, 'content', None)}") # Kept for debugging if needed
                    
                    # Check for function response errors
                    if (hasattr(event, 'content') and 
                        hasattr(event.content, 'parts') and 
                        event.content.parts and 
                        hasattr(event.content.parts[0], 'function_response') and 
                        event.content.parts[0].function_response and 
                        'error' in event.content.parts[0].function_response.response):
                        error_msg = event.content.parts[0].function_response.response['error']
                        print(f"Function error detected: {error_msg}")
                        if 'Database query error' in error_msg:
                            # Handle database query errors specifically
                            final_agent_response = "I apologize, but there seems to be an issue with the database query. Please make sure to use single quotes for text values, for example: WHERE cat_name = 'Tommy'"
                            # Consider storing this specific error response in chat_history as well
                            # store_chat_message(f"BotError: {final_agent_response}")
                            return ChatResponse(response=final_agent_response, session_id=session_id)

                    # Handle any event that has content with parts
                    if hasattr(event, 'content') and hasattr(event.content, 'parts'):
                        parts = event.content.parts
                        # print(f"Response parts: {parts}") # Kept for debugging if needed
                        for part in parts:
                            if hasattr(part, 'text') and part.text:
                                final_agent_response = part.text.strip()
                                break
                        if final_agent_response:
                            break

                # If we get here without errors, break the retry loop
                if final_agent_response:
                    break
                
            except Exception as e:
                retry_count += 1
                if 'UNAVAILABLE' in str(e) and retry_count < max_retries:
                    print(f"Model overloaded, retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                elif retry_count >= max_retries:
                    final_agent_response = "I apologize, but the service is currently experiencing high load. Please try again in a few moments."
                    # Consider storing this specific error response in chat_history
                    # store_chat_message(f"BotError: {final_agent_response}")
                    return ChatResponse(response=final_agent_response, session_id=session_id)
                else:
                    raise  # Re-raise any other exceptions

        if not final_agent_response:
            print("No final response was extracted from any event")  # Debug print
            final_agent_response = "I'm sorry, I couldn't process your request or get a clear response."

    except Exception as e:
        print(f"Error running agent: {e}")
        print(f"Full error details: {type(e).__name__}: {str(e)}")  # Enhanced error logging
        # The following comment is a consideration, not dead code.
        # Storing the error message itself in chat history might be an option here too
        # store_chat_message(f"Error in agent processing: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}. Check server logs for details.")

    # --- 4. Store Agent Response ---
    # The agent is instructed to call store_chat_message for its responses.
    # Explicitly calling it here provides redundancy.
    if final_agent_response:
        bot_message_to_store = f"Bot: {final_agent_response}"
        print(f"Attempting to store bot response: {bot_message_to_store[:100]}...")
        store_bot_msg_result = store_chat_message(bot_message_to_store)
        if isinstance(store_bot_msg_result, dict) and "error" in store_bot_msg_result:
            print(f"Failed to store bot response in DB: {store_bot_msg_result['error']}")
            # Decide if you want to raise an HTTPException here or just log
    else:
        print("No final agent response to store.")

    # --- 5. Return Response ---
    return ChatResponse(response=final_agent_response, session_id=session_id)

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI app...")
    # The following print can be very verbose, consider removing or shortening if not needed for debugging.
    # print(f"Agent instruction: {root_agent.instruction}") 
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)