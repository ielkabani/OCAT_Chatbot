import os
from dotenv import load_dotenv
from google.adk.cli.fast_api import get_fast_api_app
from agent import root_agent # Import my agent from agent.py
from tools import store_chat_message

# --- Load Environment Variables ---
load_dotenv()

# --- Run the Chatbot as a FastAPI App ---
app = get_fast_api_app(
    agent=root_agent,
    # Optional: Configure CORS if your frontend is on a different domain
    # allow_origins=["*"],
    # You might also want to configure a session database for stateful conversations
    # session_db_url="sqlite:///sessions.db", # Example for local testing
)

def handle_chat(user_message):
    # Store the user's message
    store_chat_message(user_message)
    
    # Get the agent's response
    agent_response = root_agent.run(user_message)
    
    # Extract the text/content from the agent's response
    if isinstance(agent_response, dict) and "content" in agent_response:
        response_text = agent_response["content"]
    else:
        response_text = str(agent_response)
    
    # Store the agent's response text
    store_chat_message(response_text)
    
    return agent_response

if __name__ == "__main__":
    print("Chatbot application is ready.")
    print("Ensure your .env file is configured correctly with GOOGLE_API_KEY and PostgreSQL credentials.")
