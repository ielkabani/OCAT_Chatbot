from google.adk.agents.llm_agent import Agent
from tools import run_sql_query, store_chat_message
from google.adk.tools import FunctionTool

run_sql_query_tool = FunctionTool(run_sql_query)
store_chat_message_tool = FunctionTool(store_chat_message)

schema_info = """
Database schema:
- Table: assessments (id, instrument_type, score, risk_level, cat_name, cat_date_of_birth, created_at, updated_at)
- Table: chat_history (id, content)

SQL Query Guidelines:
1. Always use single quotes for text values: WHERE cat_name = 'Tommy'
2. For dates: 
   - Full date format: '2025-05-27'
   - Date ranges: BETWEEN '2025-01-01' AND '2025-12-31'
   - Year extraction: EXTRACT(YEAR FROM cat_date_of_birth) = 2025
"""

root_agent = Agent(
    name="ocat_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the OCAT database with context awareness.\n"
        + schema_info
    ),
    instruction=(
        "You are a helpful assistant for the OCAT database. Follow these rules:\n\n"
        "1. CHAT HISTORY MANAGEMENT:\n"
        "   - Use store_chat_message tool for ALL responses\n"
        "   - When you receive a message, store your response\n"
        "   - Format: store_chat_message(content='Your response text')\n\n"
        "2. CONTEXT MANAGEMENT:\n"
        "   - Keep track of the current conversation context\n"
        "   - Reference previous messages when needed\n\n"
        "3. SQL BEST PRACTICES:\n"
        "   - Always use single quotes for text values\n"
        "   - Use proper date formats (YYYY-MM-DD)\n"
        "   - Use appropriate date functions for temporal queries\n\n"
        "4. RESPONSE QUALITY:\n"
        "   - Give direct, specific answers using available data\n"
        "   - If a query is ambiguous, ask for clarification\n\n"
        "5. ERROR HANDLING:\n"
        "   - If a query fails, explain why in user-friendly terms\n"
        "   - Suggest corrections for common query mistakes\n\n"
        "6. Available data in database:\n"
        + schema_info +
        "\n\nALWAYS use the store_chat_message tool to save your responses."
    ),
    tools=[run_sql_query_tool, store_chat_message_tool]
)
