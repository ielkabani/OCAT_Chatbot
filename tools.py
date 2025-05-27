import os
import psycopg2
import datetime
# No more explicit Tool/FunctionTool import here.
# I will just define the functions.

# --- Database Connection and Query Functions ---
def _get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname="ocat",
            user="postgres",
            password="postgres",
            host="localhost",
            port="5432"
        )
        # Ensure chat_history table exists
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        return conn
    except Exception as e:
        print(f"Database connection or table creation error: {str(e)}")
        return {"error": f"Database connection or table creation error: {str(e)}"}

def record_assessment(
    instrument_type: str,
    score: float,
    risk_level: str,
    cat_name: str,
    cat_date_of_birth: str
) -> dict:
    """
    Records a new assessment in the 'assessments' table.
    cat_date_of_birth should be in 'YYYY-MM-DD' format.
    """
    conn = _get_db_connection()
    if isinstance(conn, dict) and "error" in conn:
        return conn
    try:
        cur = conn.cursor()
        created_at = datetime.datetime.now()

        try:
            dob_date = datetime.datetime.strptime(cat_date_of_birth, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Invalid date format for cat_date_of_birth. Please use YYYY-MM-DD."}

        cur.execute(
            """
            INSERT INTO assessments (instrument_type, score, risk_level, cat_name, cat_date_of_birth, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """,
            (instrument_type, score, risk_level, cat_name, dob_date, created_at, created_at)
        )
        assessment_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "assessment_id": assessment_id}
    except Exception as e:
        print(f"Error recording assessment: {e}")
        return {"error": f"Database query error: {e}"}


def store_chat_message(content: str) -> dict:
    """
    Stores a new message in the 'chat_history' table.
    Returns a dictionary with either:
    - {"status": "success", "message_id": id} on success
    - {"error": "error message"} on failure
    """
    conn = _get_db_connection()
    if isinstance(conn, dict) and "error" in conn:
        # Error already occurred in _get_db_connection
        return conn
    
    if not conn: # Should not happen if _get_db_connection returns error dict
        return {"error": "Failed to establish database connection."}

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_history (content)
                VALUES (%s) RETURNING id;
                """,
                (content,)
            )
            message_id = cur.fetchone()[0]
            conn.commit()
            print(f"Successfully stored chat message with ID: {message_id}, Content: {content[:50]}...") # Log success
            return {"status": "success", "message_id": message_id}
    except Exception as e:
        print(f"Error storing chat message in DB: {str(e)}")
        if conn:
            try:
                conn.rollback() # Rollback on error
            except Exception as rb_e:
                print(f"Error during rollback: {rb_e}")
        return {"error": f"Database query error during store_chat_message: {str(e)}"}
    finally:
        if conn and not (isinstance(conn, dict) and "error" in conn):
            conn.close()

def get_recent_chat_history(limit: int = 5) -> list[dict]:
    """
    Retrieves the most recent chat messages from the 'chat_history' table.
    """
    conn = _get_db_connection()
    if isinstance(conn, dict) and "error" in conn:
        return conn
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, content FROM chat_history
            ORDER BY id DESC
            LIMIT %s;
            """,
            (limit,)
        )
        history = cur.fetchall()
        cur.close()
        conn.close()
        return [{"id": row[0], "content": row[1]} for row in history]
    except Exception as e:
        print(f"Error retrieving chat history: {e}")
        return {"error": f"Database query error: {e}"}

def run_sql_query(inputs: dict) -> dict:
    """
    Executes a SQL query on the OCAT database and returns the results.
    Expects a dict input: {"query": "..."}
    WARNING: This allows arbitrary SQL execution. Use with caution!
    """
    query = inputs.get("query")
    if not query:
        return {"error": "No SQL query provided in 'query' key."}
    conn = _get_db_connection()
    if isinstance(conn, dict) and "error" in conn:
        return conn
    try:
        cur = conn.cursor()
        cur.execute(query)
        # Try to fetch results if it's a SELECT
        if query.strip().lower().startswith("select"):
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            results = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    if isinstance(val, (datetime.date, datetime.datetime)):
                        row_dict[col] = val.isoformat()
                    else:
                        row_dict[col] = val
                results.append(row_dict)
            cur.close()
            conn.close()
            return {"results": results}
        else:
            conn.commit()
            cur.close()
            conn.close()
            return {"status": "success"}
    except Exception as e:
        print(f"Error running SQL query: {e}")
        return {"error": f"Database query error: {e}"}

# Export the functions directly via __all__ or simply by their names
# The agent.py will import these specific functions.
__all__ = [
    "record_assessment",
    "store_chat_message",
    "get_recent_chat_history",
    "run_sql_query",
]