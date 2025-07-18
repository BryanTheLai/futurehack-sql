# src/cogniquery_crew/tools/sql_executor_tool.py

import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import pandas as pd
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class SQLExecutorTool(BaseTool):
    name: str = "SQLExecutor"
    description: str = """Executes SQL queries on the NeonDB PostgreSQL database and returns results in CSV format.
    
    Usage: SQLExecutor(sql_query='your_sql_query')
    
    Parameters:
    - sql_query: The PostgreSQL query to execute (required)
    
    DATABASE TYPE: NeonDB PostgreSQL
    
    IMPORTANT POSTGRESQL SYNTAX GUIDELINES:
    - Use single quotes for string literals: WHERE region_name = 'Southeast Asia'
    - Use double quotes for column/table names with spaces: SELECT "column name" FROM table
    - PostgreSQL is case-sensitive for quoted identifiers
    - Use standard PostgreSQL functions: COUNT(), SUM(), AVG(), STRING_AGG(), COALESCE(), etc.
    - For multi-word string values, use single quotes: 'Southeast Asia', 'North America'
    - Use proper JOIN syntax: LEFT JOIN, INNER JOIN, etc.
    - PostgreSQL supports advanced features like window functions, CTEs, and arrays
    - Always end statements with semicolon (optional but recommended)
    
    Examples:
    - SQLExecutor(sql_query="SELECT * FROM regions WHERE region_name = 'Southeast Asia'")
    - SQLExecutor(sql_query="SELECT COUNT(*) FROM orders WHERE profit < 0")
    - SQLExecutor(sql_query="SELECT p.sub_category, SUM(o.sales) FROM products p JOIN orders o ON p.product_id = o.product_id GROUP BY p.sub_category")
    - SQLExecutor(sql_query="SELECT region_name, STRING_AGG(country, ', ') FROM regions GROUP BY region_name")"""

    def _execute_query(self, query: str, db_connection_string: str | None = None):
        """Helper function to execute a query and return a pandas DataFrame."""
        conn_str = db_connection_string or os.getenv("NEONDB_CONN_STR")
        if not conn_str:
            return "Error: NEONDB_CONN_STR is not set in environment."
        
        conn = None
        try:
            conn = psycopg2.connect(conn_str)
            return pd.read_sql_query(query, conn)
        except Exception as e:
            return f"Error executing query: {e}"
        finally:
            if conn:
                conn.close()

    def _run(self, sql_query: str, **kwargs) -> str:
        """Execute SQL query and return results."""
        logger = get_activity_logger()
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Data Scientist')
        
        # Log the SQL query being executed
        logger.log_sql_query(current_agent, sql_query)
        logger.log_tool_usage(current_agent, "SQL Executor", f"Executing SQL query")
        
        result_df = self._execute_query(sql_query)
        
        if isinstance(result_df, str):  # Error occurred
            logger.log_tool_usage(current_agent, "SQL Executor", f"Query failed: {result_df}")
            return result_df
        
        # Log successful execution with result preview
        result_csv = result_df.to_csv(index=False)
        result_preview = f"Query returned {len(result_df)} rows"
        if len(result_df) > 0:
            result_preview += f". Sample data:\n{result_df.head(3).to_string()}"
        
        logger.log_tool_usage(current_agent, "SQL Executor", f"Query executed successfully: {result_preview}")
        
        # Add instruction for the agent to use Code Interpreter for visualization
        result_with_instruction = f"""SQL Query Results (CSV format):
{result_csv}

NEXT STEP REQUIRED: Use Code Interpreter tool to create charts from this data!
- Copy the CSV data above into your Python code
- Use pd.read_csv(io.StringIO(csv_data)) to convert to DataFrame
- Create visualizations with matplotlib.pyplot
- Save charts with plt.savefig('output/chart_1.png')

REMEMBER: Charts will only appear in the UI if you use Code Interpreter + plt.savefig()!
"""
        
        return result_with_instruction
