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
    name: str = "DatabaseTools"
    description: str = """A comprehensive suite of tools for interacting with a PostgreSQL database.
    
    Available operations:
    1. Get comprehensive schema: action='get_schema' - Returns tables, columns, data types, primary keys, foreign keys, and relationships
    2. Get sample data: action='get_sample_data', table_name='your_table' - Returns sample rows from a specific table
    3. Execute SQL query: sql_query='your_query' - Executes any SQL query and returns results
    
    PARAMETER USAGE:
    - For schema: DatabaseTools(action='get_schema')
    - For sample data: DatabaseTools(action='get_sample_data', table_name='regions')
    - For SQL query: DatabaseTools(sql_query='SELECT * FROM regions LIMIT 5')
    
    The connection string is loaded automatically from environment variables."""

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
        Returns the comprehensive schema of the database as a string.
        The schema includes table names, columns, data types, primary keys, foreign keys, and relationships.
        """
        logger = get_activity_logger()
        
        # Determine which agent is calling this
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Unknown Agent')
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Getting comprehensive database schema")
        
        # Query 1: Get basic table and column information
        columns_query = """
        SELECT table_name, column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        
        # Query 2: Get primary key information
        pk_query = """
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' 
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.ordinal_position;
        """
        
        # Query 3: Get foreign key relationships
        fk_query = """
        SELECT
            tc.table_name as source_table,
            kcu.column_name as source_column,
            ccu.table_name as target_table,
            ccu.column_name as target_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu 
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name, kcu.column_name;
        """
        
        logger.log_sql_query(current_agent, "Schema analysis queries (columns, primary keys, foreign keys)")
        
        # Execute all queries
        columns_df = self._execute_query(columns_query, db_connection_string)
        pk_df = self._execute_query(pk_query, db_connection_string)
        fk_df = self._execute_query(fk_query, db_connection_string)
        
        # Check for errors
        if isinstance(columns_df, str):
            logger.log_tool_usage(current_agent, "Database Tools", f"Schema query failed: {columns_df}")
            return columns_df
        
        # Build comprehensive schema string
        schema_str = "=== DATABASE SCHEMA ANALYSIS ===\n\n"
        
        # Get all tables
        tables = columns_df['table_name'].unique()
        
        # Primary keys lookup
        pk_lookup = {}
        if not isinstance(pk_df, str) and len(pk_df) > 0:
            for _, row in pk_df.iterrows():
                table = row['table_name']
                if table not in pk_lookup:
                    pk_lookup[table] = []
                pk_lookup[table].append(row['column_name'])
        
        # Foreign keys lookup
        fk_lookup = {}
        if not isinstance(fk_df, str) and len(fk_df) > 0:
            for _, row in fk_df.iterrows():
                source_table = row['source_table']
                if source_table not in fk_lookup:
                    fk_lookup[source_table] = []
                fk_lookup[source_table].append({
                    'source_column': row['source_column'],
                    'target_table': row['target_table'],
                    'target_column': row['target_column']
                })
        
        # Build detailed schema for each table
        for table in sorted(tables):
            schema_str += f"📊 Table: {table}\n"
            
            # Add columns
            table_columns = columns_df[columns_df['table_name'] == table]
            for _, col in table_columns.iterrows():
                column_name = col['column_name']
                data_type = col['data_type']
                is_nullable = col['is_nullable']
                default_val = col['column_default']
                
                # Mark primary keys
                pk_marker = " [PRIMARY KEY]" if table in pk_lookup and column_name in pk_lookup[table] else ""
                
                # Mark foreign keys
                fk_marker = ""
                if table in fk_lookup:
                    for fk in fk_lookup[table]:
                        if fk['source_column'] == column_name:
                            fk_marker = f" [FK → {fk['target_table']}.{fk['target_column']}]"
                            break
                
                nullable_info = "" if is_nullable == "YES" else " NOT NULL"
                default_info = f" DEFAULT {default_val}" if default_val else ""
                
                schema_str += f"  - {column_name} ({data_type}){pk_marker}{fk_marker}{nullable_info}{default_info}\n"
            
            schema_str += "\n"
        
        # Add relationships summary
        if not isinstance(fk_df, str) and len(fk_df) > 0:
            schema_str += "🔗 TABLE RELATIONSHIPS:\n"
            for _, row in fk_df.iterrows():
                schema_str += f"  - {row['source_table']}.{row['source_column']} → {row['target_table']}.{row['target_column']}\n"
            schema_str += "\n"
        
        # Add summary statistics
        schema_str += f"📈 SCHEMA SUMMARY:\n"
        schema_str += f"  - Total tables: {len(tables)}\n"
        schema_str += f"  - Total columns: {len(columns_df)}\n"
        schema_str += f"  - Primary key constraints: {len(pk_df) if not isinstance(pk_df, str) else 0}\n"
        schema_str += f"  - Foreign key relationships: {len(fk_df) if not isinstance(fk_df, str) else 0}\n"
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Retrieved comprehensive schema for {len(tables)} tables with relationships")
        return schema_str

    def get_sample_data(self, table_name: str, limit: int = 5, db_connection_string: str | None = None) -> str:
        """
        Returns sample data from a specific table to help understand the data structure and content.
        """
        logger = get_activity_logger()
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Unknown Agent')
        
        # Validate table name to prevent SQL injection
        if not table_name.replace('_', '').isalnum():
            return "Error: Invalid table name. Only alphanumeric characters and underscores allowed."
        
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Getting sample data from table: {table_name}")
        logger.log_sql_query(current_agent, query)
        
        sample_df = self._execute_query(query, db_connection_string)
        
        if isinstance(sample_df, str):
            logger.log_tool_usage(current_agent, "Database Tools", f"Sample data query failed: {sample_df}")
            return sample_df
        
        if len(sample_df) == 0:
            return f"Table {table_name} contains no data."
        
        # Format the sample data nicely
        result = f"📋 SAMPLE DATA from table '{table_name}' (showing {len(sample_df)} rows):\n\n"
        result += sample_df.to_string(index=False)
        
        logger.log_tool_usage(current_agent, "Database Tools", f"Retrieved {len(sample_df)} sample rows from {table_name}")
        return result

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
    
    def _run(self, **kwargs) -> str:
        """
        Abstract method implementation for BaseTool. 
        
        Supports multiple operations:
        1. SQL query execution: provide 'sql_query' parameter
        2. Schema retrieval: provide 'action': 'get_schema' 
        3. Sample data: provide 'action': 'get_sample_data' and 'table_name'
        """
        # Use connection string from tools_context if provided, else fallback to .env
        db_str = kwargs.get('db_connection_string')
        
        # Check for action parameter specifically
        action = kwargs.get('action')
        sql_query = kwargs.get('sql_query')
        table_name = kwargs.get('table_name')
        
        # DEBUG: Add logging to see what's being called
        print(f"DEBUG: _run called with kwargs: {kwargs}")
        print(f"DEBUG: action='{action}', sql_query='{sql_query}', table_name='{table_name}'")
        
        # Priority order: sql_query > action > default
        if sql_query:
            # Execute SQL query
            print(f"DEBUG: Executing SQL query: {sql_query}")
            result = self.run_sql_query(sql_query, db_str)
            print(f"DEBUG: SQL query result length: {len(result)}")
            return result
        elif action == 'get_schema':
            print(f"DEBUG: Getting schema")
            result = self.get_schema(db_str)
            print(f"DEBUG: Schema result length: {len(result)}")
            return result
        elif action == 'get_sample_data':
            limit = kwargs.get('limit', 5)
            if not table_name:
                return "Error: table_name is required for get_sample_data action"
            print(f"DEBUG: Getting sample data from table '{table_name}' with limit {limit}")
            result = self.get_sample_data(table_name, limit, db_str)
            print(f"DEBUG: Sample data result length: {len(result)}")
            print(f"DEBUG: Sample data result preview: {result[:200]}")
            # Make sure we're not accidentally returning schema
            if "TABLE SCHEMA" in result or "table_name" in result.lower():
                print("DEBUG: WARNING - Sample data result contains schema-like content!")
            return result
        elif not action and not sql_query and not table_name:
            # Default to schema retrieval for business analyst
            print(f"DEBUG: Defaulting to schema retrieval")
            result = self.get_schema(db_str)
            print(f"DEBUG: Default schema result length: {len(result)}")
            return result
        else:
            error_msg = f"Error: Unrecognized action '{action}' or missing parameters. Available actions: get_schema, get_sample_data, or provide sql_query"
            print(f"DEBUG: {error_msg}")
            return error_msg
