from google.adk.agents.llm_agent import Agent
from .tools import run_sql_query
from google.adk.tools import FunctionTool

run_sql_query_tool = FunctionTool(run_sql_query)
schema_info = """
Database schema:
- Table: assessments (id, instrument_type, score, risk_level, cat_name, cat_date_of_birth, created_at, updated_at)
- Table: chat_history (id, content)
"""
root_agent = Agent(
    name="ocat_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the OCAT database.\n"
        + schema_info
    ),
    instruction=(
        "You have access to the OCAT database via the run_sql_query tool. "
        "Use it to answer any question about the database, including retrieving, searching, or summarizing data.\n"
        "Refer to the following schema for table and column names:\n"
        + schema_info
    ),
    tools=[run_sql_query_tool]
)