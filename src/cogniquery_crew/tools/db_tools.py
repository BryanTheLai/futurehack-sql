# src/cogniquery_crew/tools/db_tools.py

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
import psycopg2
import pandas as pd
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class DatabaseTools(BaseTool):
    name: str = "Database Tools"
    description: str = "A suite of tools for interacting with a PostgreSQL database. Provide only the SQL query; the connection string is loaded automatically."

    def _execute_query(self, query: str, db_connection_string: str | None = None):
        """Helper function to execute a query and return a pandas DataFrame."""
        # Determine connection string: passed in or from environment
        conn_str = db_connection_string or os.getenv("NEONDB_CONN_STR")
        if not conn_str:
            return "Error: NEONDB_CONN_STR is not set in environment or passed to the tool."
        conn = None
        try:
            conn = psycopg2.connect(conn_str)
            return pd.read_sql_query(query, conn)
        except Exception as e:
            # Return the error message as a string if the query fails
            return f"Error executing query: {e}"
        finally:
            if conn:
                conn.close()

    def get_schema(self, db_connection_string: str | None = None) -> str:
        """
        Returns the schema of the database as a string.
        The schema includes table names and their respective columns.
        """
        logger = get_activity_logger()
        query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public';
        """
        
        # Determine which agent is calling this (could be Business Analyst or SQL Generator)
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Unknown Agent')
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Getting database schema")
        logger.log_sql_query(current_agent, query)
        
        schema_df = self._execute_query(query, db_connection_string)
        
        if isinstance(schema_df, str): # Error occurred
            logger.log_tool_usage(current_agent, "Database Tools", f"Schema query failed: {schema_df}")
            return schema_df

        schema_str = "Database Schema:\n"
        for table in schema_df['table_name'].unique():
            schema_str += f"\nTable: {table}\n"
            columns = schema_df[schema_df['table_name'] == table]
            for _, col in columns.iterrows():
                schema_str += f"  - {col['column_name']} ({col['data_type']})\n"
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Retrieved schema for {len(schema_df['table_name'].unique())} tables")
        return schema_str

    def run_sql_query(self, sql_query: str, db_connection_string: str | None = None) -> str:
        """
        Executes a given SQL query on the database and returns the result
        as a CSV formatted string.
        If the query fails, it returns the error message.
        """
        logger = get_activity_logger()
        
        # Log the SQL query being executed
        logger.log_sql_query("Data Analyst", sql_query)
        logger.log_tool_usage("Data Analyst", "Database Tools", f"Executing SQL query")
        
        result_df = self._execute_query(sql_query, db_connection_string)
        
        if isinstance(result_df, str): # Error occurred
            logger.log_tool_usage("Data Analyst", "Database Tools", f"Query failed: {result_df}")
            return result_df
        
        # Log successful execution with result preview
        result_csv = result_df.to_csv(index=False)
        result_preview = f"Query returned {len(result_df)} rows"
        if len(result_df) > 0:
            result_preview += f". Sample data:\n{result_df.head(3).to_string()}"
        
        logger.log_tool_usage("Data Analyst", "Database Tools", f"Query executed successfully: {result_preview}")
        
        return result_csv
    
    def _run(self, sql_query: str, **kwargs) -> str:
        """
        Abstract method implementation for BaseTool. Executes the SQL query and returns CSV or error.
        The database connection is automatically loaded from the NEONDB_CONN_STR environment variable.
        """
        # Use connection string from tools_context if provided, else fallback to .env
        db_str = kwargs.get('db_connection_string')
        return self.run_sql_query(sql_query, db_str)
