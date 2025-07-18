# src/cogniquery_crew/tools/db_tools.py

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()
import psycopg2
import pandas as pd
from crewai.tools import BaseTool

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
        query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public';
        """
        schema_df = self._execute_query(query, db_connection_string)
        
        if isinstance(schema_df, str): # Error occurred
            return schema_df

        schema_str = "Database Schema:\n"
        for table in schema_df['table_name'].unique():
            schema_str += f"\nTable: {table}\n"
            columns = schema_df[schema_df['table_name'] == table]
            for _, col in columns.iterrows():
                schema_str += f"  - {col['column_name']} ({col['data_type']})\n"
        return schema_str

    def run_sql_query(self, sql_query: str, db_connection_string: str | None = None) -> str:
        """
        Executes a given SQL query on the database and returns the result
        as a CSV formatted string.
        If the query fails, it returns the error message.
        """
        result_df = self._execute_query(sql_query, db_connection_string)
        
        if isinstance(result_df, str): # Error occurred
            return result_df
            
        return result_df.to_csv(index=False)
    
    def _run(self, sql_query: str, **kwargs) -> str:
        """
        Abstract method implementation for BaseTool. Executes the SQL query and returns CSV or error.
        The database connection is automatically loaded from the NEONDB_CONN_STR environment variable.
        """
        # Use connection string from tools_context if provided, else fallback to .env
        db_str = kwargs.get('db_connection_string')
        return self.run_sql_query(sql_query, db_str)
