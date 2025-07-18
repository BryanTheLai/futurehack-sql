# src/cogniquery_crew/tools/schema_explorer_tool.py

import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2
import pandas as pd
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class SchemaExplorerTool(BaseTool):
    name: str = "SchemaExplorer"
    description: str = """Gets comprehensive database schema information from NeonDB PostgreSQL including tables, columns, data types, primary keys, foreign keys, and relationships. 
    
    Usage: SchemaExplorer() - no parameters needed.
    
    DATABASE TYPE: NeonDB PostgreSQL"""

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

    def _run(self, **kwargs) -> str:
        """Get comprehensive database schema."""
        logger = get_activity_logger()
        current_status = logger.get_current_status()
        current_agent = current_status.get('current_agent', 'Unknown Agent')
        
        logger.log_tool_usage(current_agent, "Schema Explorer", "Getting comprehensive database schema")
        
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
        columns_df = self._execute_query(columns_query)
        pk_df = self._execute_query(pk_query)
        fk_df = self._execute_query(fk_query)
        
        # Check for errors
        if isinstance(columns_df, str):
            logger.log_tool_usage(current_agent, "Schema Explorer", f"Schema query failed: {columns_df}")
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
                table = row['source_table']
                if table not in fk_lookup:
                    fk_lookup[table] = []
                fk_lookup[table].append({
                    'source_column': row['source_column'],
                    'target_table': row['target_table'],
                    'target_column': row['target_column']
                })
        
        # Build detailed schema for each table
        for table in sorted(tables):
            table_columns = columns_df[columns_df['table_name'] == table]
            schema_str += f"📊 TABLE: {table}\n"
            
            # Columns
            for _, col in table_columns.iterrows():
                pk_indicator = " (PK)" if table in pk_lookup and col['column_name'] in pk_lookup[table] else ""
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f", DEFAULT: {col['column_default']}" if col['column_default'] else ""
                schema_str += f"  • {col['column_name']}: {col['data_type']}{pk_indicator} ({nullable}{default})\n"
            
            # Foreign keys
            if table in fk_lookup:
                schema_str += f"  Foreign Keys:\n"
                for fk in fk_lookup[table]:
                    schema_str += f"    • {fk['source_column']} -> {fk['target_table']}.{fk['target_column']}\n"
            
            schema_str += "\n"
        
        # Add relationships summary
        if not isinstance(fk_df, str) and len(fk_df) > 0:
            schema_str += "🔗 TABLE RELATIONSHIPS:\n"
            for _, row in fk_df.iterrows():
                schema_str += f"  • {row['source_table']}.{row['source_column']} -> {row['target_table']}.{row['target_column']}\n"
            schema_str += "\n"
        
        # Add summary statistics
        schema_str += f"📈 SCHEMA SUMMARY:\n"
        schema_str += f"  - Total tables: {len(tables)}\n"
        schema_str += f"  - Total columns: {len(columns_df)}\n"
        schema_str += f"  - Primary key constraints: {len(pk_df) if not isinstance(pk_df, str) else 0}\n"
        schema_str += f"  - Foreign key relationships: {len(fk_df) if not isinstance(fk_df, str) else 0}\n"
        
        logger.log_tool_usage(current_agent, "Schema Explorer", f"Retrieved comprehensive schema for {len(tables)} tables with relationships")
        return schema_str
