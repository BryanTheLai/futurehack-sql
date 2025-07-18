# src/cogniquery_crew/tools/db_tools.py

import os
import psycopg2
import pandas as pd
from crewai_tools import BaseTool

class DatabaseTools(BaseTool):
    name: str = "Database Tools"
    description: str = "A suite of tools for interacting with a PostgreSQL database."

    def _execute_query(self, db_connection_string: str, query: str):
        """Helper function to execute a query and return a pandas DataFrame."""
        conn = None
        try:
            conn = psycopg2.connect(db_connection_string)
            return pd.read_sql_query(query, conn)
        except Exception as e:
            # Return the error message as a string if the query fails
            return f"Error executing query: {e}"
        finally:
            if conn:
                conn.close()
    
    def get_schema(self, db_connection_string: str) -> str:
        """
        Returns the schema of the database as a string.
        The schema includes table names and their respective columns.
        """
        query = """
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public';
        """
        schema_df = self._execute_query(db_connection_string, query)
        
        if isinstance(schema_df, str): # Error occurred
            return schema_df

        schema_str = "Database Schema:\n"
        for table in schema_df['table_name'].unique():
            schema_str += f"\nTable: {table}\n"
            columns = schema_df[schema_df['table_name'] == table]
            for _, col in columns.iterrows():
                schema_str += f"  - {col['column_name']} ({col['data_type']})\n"
        return schema_str

    def run_sql_query(self, sql_query: str, db_connection_string: str) -> str:
        """
        Executes a given SQL query on the database and returns the result
        as a CSV formatted string.
        If the query fails, it returns the error message.
        """
        result_df = self._execute_query(db_connection_string, sql_query)
        
        if isinstance(result_df, str): # Error occurred
            return result_df
            
        return result_df.to_csv(index=False)
