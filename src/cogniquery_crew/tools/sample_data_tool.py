# src/cogniquery_crew/tools/sample_data_tool.py

import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import pandas as pd
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class SampleDataTool(BaseTool):
    name: str = "SampleData"
    description: str = """Gets sample data from a specific table in the NeonDB PostgreSQL database to understand data patterns and content.
    
    Usage: SampleData(table_name='your_table_name', limit=5)
    
    Parameters:
    - table_name: Name of the table to get sample data from (required)
    - limit: Number of rows to return (optional, default is 5)
    
    DATABASE TYPE: NeonDB PostgreSQL
    
    Example: SampleData(table_name='regions', limit=3)"""

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

    def _run(self, table_name: str, limit: int = 5, **kwargs) -> str:
        """Get sample data from a specific table."""
        logger = get_activity_logger()
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Unknown Agent')
        
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            return "Error: Invalid table name. Only alphanumeric characters and underscores allowed."
        
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        
        logger.log_tool_usage(current_agent, "Sample Data", f"Getting sample data from table: {table_name}")
        logger.log_sql_query(current_agent, query)
        
        sample_df = self._execute_query(query)
        
        if isinstance(sample_df, str):
            logger.log_tool_usage(current_agent, "Sample Data", f"Sample data query failed: {sample_df}")
            return sample_df
        
        if len(sample_df) == 0:
            return f"Table {table_name} contains no data."
        
        # Format the sample data nicely
        result = f"📋 SAMPLE DATA from table '{table_name}' (showing {len(sample_df)} rows):\n\n"
        result += sample_df.to_string(index=False)
        
        logger.log_tool_usage(current_agent, "Sample Data", f"Retrieved {len(sample_df)} sample rows from {table_name}")
        return result
