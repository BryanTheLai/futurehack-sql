<Date> July 19, 2025 00:55</Date>

```app.py
# app.py

import os
import time
import json
import streamlit as st
from dotenv import load_dotenv
from src.cogniquery_crew.crew import CogniQueryCrew
from src.cogniquery_crew.tools.activity_logger import get_activity_logger

# Load environment variables
load_dotenv()
# Ensure output directory exists
os.makedirs("output", exist_ok=True)

def cleanup_output_files():
    """Removes generated files from the output directory to keep it clean."""
    # Clean generated files from output directory
    file_patterns = ["chart.png", "final_report.md", "final_report.pdf", "activity_log.json"]
    
    for pattern in file_patterns:
        file_path = f"output/{pattern}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            except Exception as e:
                print(f"Could not remove {file_path}: {e}")
    
    # Also remove any other PNG files that might have been created
    if os.path.exists("output"):
        for file in os.listdir("output"):
            if file.endswith('.png'):
                try:
                    os.remove(f"output/{file}")
                    print(f"Cleaned up chart file: {file}")
                except Exception as e:
                    print(f"Could not remove chart file {file}: {e}")

def display_activity_log():
    """Display the current activity log in the UI."""
    try:
        logger = get_activity_logger()
        activities = logger.get_activities()
        status = logger.get_current_status()
        
        if not activities and not status.get('current_agent'):
            return
        
        st.subheader("🔍 Agent Activity Log")
        st.write("*Watch your AI agents work in real-time! All SQL queries and Python code execution are logged below.*")
        
        # Current status indicator
        if status.get('current_agent') and status.get('current_task'):
            st.info(f"🤖 **Currently Active:** {status['current_agent']} is working on {status['current_task'].replace('_', ' ')}")
        
        # Activity summary
        sql_count = len([a for a in activities if a.get('type') == 'sql_query'])
        python_count = len([a for a in activities if a.get('type') == 'python_code'])
        task_count = len([a for a in activities if a.get('type') == 'task_start'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("SQL Queries", sql_count)
        with col2:
            st.metric("Python Scripts", python_count)
        with col3:
            st.metric("Tasks Started", task_count)
        
        if not activities:
            return
            
        st.divider()
        
        for i, activity in enumerate(activities):
            timestamp = activity.get('timestamp', '').split('T')[1].split('.')[0] if activity.get('timestamp') else ''
            agent = activity.get('agent', 'Unknown')
            activity_type = activity.get('type', 'unknown')
            content = activity.get('content', '')
            details = activity.get('details', {})
            
            # Create different styling for different activity types
            if activity_type == 'sql_query':
                st.markdown(f"**🗄️ [{timestamp}] {agent} - SQL Query Execution**")
                st.code(content, language='sql')
                if details.get('result_preview'):
                    st.success("✅ Query executed successfully")
                    with st.expander("View Query Results"):
                        st.text(details['result_preview'])
                        
            elif activity_type == 'python_code':
                st.markdown(f"**🐍 [{timestamp}] {agent} - Python Code Execution**")
                st.code(content, language='python')
                if details.get('result'):
                    with st.expander("View Execution Results"):
                        st.text(details['result'])
                        
            elif activity_type == 'task_start':
                st.markdown(f"**🎯 [{timestamp}] {agent} - Task Started**")
                st.info(f"**{details.get('task_name', 'Unknown Task')}**")
                with st.expander("Task Description"):
                    st.write(details.get('description', content))
                    
            elif activity_type == 'tool_usage':
                st.markdown(f"**🛠️ [{timestamp}] {agent} - {details.get('tool_name', 'Tool')} Usage**")
                st.write(f"**Action:** {details.get('action', content)}")
                if details.get('result'):
                    with st.expander("Tool Result"):
                        st.text(details['result'])
            else:
                st.markdown(f"**ℹ️ [{timestamp}] {agent} - {activity_type.replace('_', ' ').title()}**")
                st.text(content)
                if details:
                    with st.expander("Details"):
                        st.json(details)
            
            st.divider()
            
    except Exception as e:
        st.error(f"Error displaying activity log: {e}")

st.set_page_config(page_title="CogniQuery", page_icon="🤖")
st.title("CogniQuery 🤖")
st.subheader("Your AI Data Scientist")

st.write(
    "Welcome to CogniQuery! Connect to your NeonDB database, ask a question in plain English, "
    "and receive a comprehensive report with charts and insights."
)

# --- User Inputs ---
st.sidebar.header("Configuration")
# Use blank inputs to hide secrets; fallback to .env defaults securely
openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", 
    type="password", 
    value="",
    placeholder="Leave blank to use default key securely stored in .env"
)
db_connection_string = st.sidebar.text_input(
    "NeonDB Connection String",
    value="",
    placeholder="Leave blank to use default connection string from .env"
)

# --- Recommended Queries Section ---
st.header("💡 Recommended Queries")
st.write("*New to the dataset? Start with these sample questions to explore your data:*")

# Sample questions with engaging descriptions
sample_queries = [
    {
        "title": "🔍 Investigate Southeast Asia Profit Issues",
        "description": "Identify regional performance problems and root cause",
        "query": "Our profit in Southeast Asia is a disaster. Find the top 3 sub-categories that are losing the most money in that region. Show me their total sales and profit, and investigate if high discounts are the cause. Show with visualizations"
    },
    {
        "title": "💰 Discount Impact Analysis",
        "description": "Understand how the discounts affect bottom line",
        "query": "Show me the relationship between discount levels and profitability with visualization. Are high discounts killing our margins? Create a chart showing profit vs discount percentage."
    }
]

# Display sample queries in a nice grid
cols = st.columns(2)
for i, sample in enumerate(sample_queries):
    with cols[i % 2]:
        with st.container():
            st.markdown(f"**{sample['title']}**")
            st.caption(sample['description'])
            if st.button(f"Use This Query", key=f"sample_{i}", use_container_width=True):
                st.session_state.selected_query = sample['query']

st.header("🤖 Ask Your Data a Question")

# Use selected query if available
default_query = st.session_state.get('selected_query', '')
query = st.text_area(
    "Enter your question here:",
    value=default_query,
    placeholder="e.g., 'What were our total sales per month for the last year?'",
    height=150,
)


# Initialize session state for button control
if 'report_generating' not in st.session_state:
    st.session_state.report_generating = False

# Generate Report button with conditional disable
generate_button_disabled = st.session_state.report_generating
button_text = "⏳ Generating Report..." if st.session_state.report_generating else "Generate Report"

if st.button(button_text, disabled=generate_button_disabled):
    # Set the generating state to True
    st.session_state.report_generating = True
    
    # Use user inputs or fall back to environment variables
    final_openai_key = openai_api_key.strip() or os.getenv("OPENAI_API_KEY", "")
    final_db_conn = db_connection_string.strip() or os.getenv("NEONDB_CONN_STR", "")
    
    if not final_openai_key or not final_db_conn or not query:
        st.error("Please provide all required inputs: OpenAI Key, DB Connection String, and your query.")
        # Reset the generating state if there's an error
        st.session_state.report_generating = False
    else:
        # Set the API key for the current process
        os.environ["OPENAI_API_KEY"] = final_openai_key
        os.environ["NEONDB_CONN_STR"] = final_db_conn
        
        # Clean up old files before running
        cleanup_output_files()

        # Create placeholder for activity log
        activity_placeholder = st.empty()
        status_placeholder = st.empty()

        with status_placeholder:
            st.info("🤖 Your AI Data Scientist is starting up...")

        try:
            # Initialize and run the crew
            cogniquery_crew = CogniQueryCrew(db_connection_string=final_db_conn)
            
            # Run the crew in a separate process while updating the UI
            import threading
            result = [None]  # Use list to allow modification in nested function
            error = [None]
            
            def run_crew():
                try:
                    result[0] = cogniquery_crew.crew().kickoff(inputs={'query': query})
                except Exception as e:
                    error[0] = e
            
            # Start crew execution in background
            crew_thread = threading.Thread(target=run_crew)
            crew_thread.start()
            
            # Update activity log while crew is running
            while crew_thread.is_alive():
                with activity_placeholder.container():
                    display_activity_log()
                time.sleep(2)  # Update every 2 seconds
                
            # Wait for thread to complete
            crew_thread.join()
            
            # Final update of activity log
            with activity_placeholder.container():
                display_activity_log()
            
            if error[0]:
                raise error[0]
                
            with status_placeholder:
                st.success("✅ Report generated successfully!")
            
            # Reset the generating state on success
            st.session_state.report_generating = False

            # Display the generated markdown report
            st.subheader("📊 Generated Analysis Report")
            st.markdown(result[0].raw, unsafe_allow_html=True)
            
            # Display all chart images with improved detection
            output_dir = "output"
            chart_files = []
            
            # Debug: List all files in output directory
            try:
                if os.path.exists(output_dir):
                    output_files = os.listdir(output_dir)
                    chart_files = [f for f in output_files if f.endswith('.png')]
                    st.write(f"📁 Files in output directory: {output_files}")
                    st.write(f"📊 Chart files found: {chart_files}")
                else:
                    st.write("📁 Output directory does not exist")
            except Exception as e:
                st.write(f"📁 Could not list output directory: {e}")
            
            # Display charts
            if chart_files:
                st.subheader("📈 Generated Charts")
                
                # Sort chart files for consistent display order
                chart_files.sort()
                
                # Display each chart
                for i, chart_file in enumerate(chart_files):
                    chart_path = os.path.join(output_dir, chart_file)
                    try:
                        # Create a more descriptive caption
                        chart_name = chart_file.replace('.png', '').replace('_', ' ').title()
                        st.image(chart_path, caption=f"{chart_name}", use_container_width=True)
                        
                        # Add some spacing between charts
                        if i < len(chart_files) - 1:
                            st.write("")
                            
                    except Exception as e:
                        st.error(f"❌ Error displaying chart {chart_file}: {e}")
                
                st.success(f"✅ {len(chart_files)} chart(s) displayed successfully!")
                
            else:
                st.warning("⚠️ No charts were generated or could not be found. Check the activity log for details.")
                st.write(f"Expected charts location: {os.path.abspath(output_dir)}")
                if os.path.exists(output_dir):
                    output_contents = os.listdir(output_dir)
                    st.write(f"Output directory contents: {output_contents}")
                else:
                    st.write("Output directory does not exist")

        except Exception as e:
            with status_placeholder:
                st.error(f"❌ An error occurred: {e}")
            # Reset the generating state on error
            st.session_state.report_generating = False
        finally:
            # Ensure the generating state is reset
            st.session_state.report_generating = False
            # Keep the activity log visible after completion
            pass

st.sidebar.info(
    "**How it works:**\n"
    "1. **Business Analyst:** Refines your query and explores database schema.\n"
    "2. **Data Scientist:** Writes SQL queries, analyzes data, and creates charts.\n"
    "3. **Communications Strategist:** Compiles the final report.\n\n"
    "**🔍 Activity Log:** Watch the agents work in real-time! "
    "You'll see all SQL queries, tool usage, and progress updates as they happen.\n\n"
    "**💡 Configuration:** API keys and DB connection can be set in .env file "
    "or entered above. Values entered above will override .env settings."
)
```

```code_scraper.py
import os
import sys
from datetime import datetime

# --- Configuration ---
# HARDCODE the exact, full path to the directory you want to scan.
# Use a raw string (r"...") or double backslashes (\\) for Windows paths.
TARGET_DIRECTORY = r"C:\Users\wbrya\OneDrive\Documents\GitHub\futurehack-sql"

# Set the name for the output file.
# It will be created in the directory where you run the script.
# Using .md extension because the output format is Markdown.
OUTPUT_FILENAME = "consolidated_code.md"

# Optional: List of directory names to completely skip during scanning
# Add any other folders within the TARGET_DIRECTORY you want to ignore.
DIRECTORIES_TO_SKIP = {'images','output','.venv','dataset','data','.git', '.vscode', '.idea', 'target', 'build', '__pycache__', 'node_modules', 'output_folder'}

# Optional: List of specific file names (case-sensitive) to completely skip
# regardless of which directory they are in.
FILES_TO_SKIP = {'scraper.py','consolidated_code.md','test_api.ipynb','test_pdf copy.ipynb','__init__.py', 'setup.py', '.env', '.env.example', 'README.md'}
# --- End Configuration ---


def consolidate_to_markdown(root_dir, output_filepath, dirs_to_skip, files_to_skip):
    """
    Walks through the specified root directory and consolidates file contents
    into a single Markdown file using triple-backtick code blocks.

    Skips specified directories and specific files by name, and hidden files/folders.

    Args:
        root_dir (str): The absolute path to the directory to scan.
        output_filepath (str): The absolute path to the output Markdown file.
        dirs_to_skip (set): A set of directory names to skip.
        files_to_skip (set): A set of file names to skip.
    """
    abs_root_dir = os.path.abspath(root_dir)

    # --- Input Validation ---
    if not os.path.isdir(abs_root_dir):
        print(f"Error: Target directory not found at the specified path:")
        print(f"  '{abs_root_dir}'")
        print("\nPlease check the TARGET_DIRECTORY variable in the script.")
        return False # Indicate failure
    # --- End Input Validation ---

    print(f"Scanning directory: {abs_root_dir}")
    print(f"Output file:      {output_filepath}")
    print(f"Skipping dirs:    {', '.join(dirs_to_skip) if dirs_to_skip else 'None'}")
    print(f"Skipping files:   {', '.join(files_to_skip) if files_to_skip else 'None'}") # Added print for new list
    print("-" * 30)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            # Add the current date to the output file
            outfile.write(f"<Date> {datetime.now().strftime('%B %d, %Y %H:%M')}</Date>\n\n")
            file_count = 0
            # os.walk efficiently traverses the directory tree
            for dirpath, dirnames, filenames in os.walk(abs_root_dir, topdown=True):
                # Modify dirnames in-place to prevent os.walk from descending into skipped directories
                dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in dirs_to_skip]

                # Sort filenames for consistent order (optional, but nice)
                filenames.sort()

                for filename in filenames:
                    # Skip hidden files
                    if filename.startswith('.'):
                       continue
                    # --- Modification: Skip files in the exclusion list ---
                    if filename in files_to_skip:
                       print(f"  Skipping file: {filename}") # Optional: Add log for skipped files
                       continue
                    # --- End Modification ---


                    full_path = os.path.join(dirpath, filename)
                    # Calculate the relative path from the root directory being scanned
                    relative_path = os.path.relpath(full_path, abs_root_dir)
                    # Ensure consistent use of forward slashes for the Markdown path header
                    relative_path = relative_path.replace(os.sep, '/')

                    print(f"  Adding: {relative_path}")
                    file_count += 1

                    try:
                        # Read the content of the current file
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()

                        # --- Write the formatted Markdown output ---
                        outfile.write(f"```{relative_path}\n") # Start code block with relative path
                        outfile.write(content)                # The actual file content
                        # Ensure there's a newline before the closing backticks if content exists
                        if content and not content.endswith('\n'):
                            outfile.write("\n")
                        outfile.write("```\n\n")               # End code block and add blank line for separation
                        # --- End Markdown output ---

                    except Exception as e:
                        print(f"    Error reading file {full_path}: {e}")
                        # Still write header, but note error inside code block
                        outfile.write(f"```{relative_path}\n")
                        outfile.write(f"*** Error reading file: {e} ***")
                        outfile.write("\n```\n\n")

            print("-" * 30)
            if file_count > 0:
                print(f"Consolidation complete. Added {file_count} files.")
                print(f"Output saved to '{output_filepath}'.")
            else:
                 print(f"Warning: No files found in '{abs_root_dir}' (excluding skipped dirs/files).")
            return True # Indicate success

    except IOError as e:
        print(f"Error: Could not write to output file {output_filepath}: {e}")
        return False # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False # Indicate failure


# --- Main execution part ---
if __name__ == "__main__":
    print("Starting file consolidation script...")
    print("-" * 30)

    # Use the hardcoded target directory from configuration
    target_dir_path = TARGET_DIRECTORY

    # Determine where to save the output file (in the current working directory)
    try:
        # Get the current working directory from where the script is executed
        script_run_dir = os.getcwd()
    except Exception as e:
         print(f"Fatal Error: Could not get current working directory: {e}")
         print("Cannot determine where to save the output file.")
         sys.exit(1) # Exit if we can't figure out where to save the file

    # Construct the full path for the output file
    output_file_path = os.path.join(script_run_dir, OUTPUT_FILENAME)

    print(f"Target directory:   {target_dir_path}")
    print(f"Output file will be created at: {output_file_path}")

    # Run the consolidation function, passing the new exclusion list
    success = consolidate_to_markdown(target_dir_path, output_file_path, DIRECTORIES_TO_SKIP, FILES_TO_SKIP)

    print("-" * 30)
    if success:
        print("Script finished successfully.")
    else:
        print("Script finished with errors.")

    # Optional: Pause for visibility when run by double-clicking
    # input("\nPress Enter to exit...")
```

```requirements.txt
# requirements.txt

crewai[tools]

openai
streamlit
python-dotenv
psycopg2-binary
pandas
matplotlib
weasyprint
markdown-it-py
```

```scripts/dataset.sql
-- Sample E-commerce Dataset for CogniQuery Demo
-- This dataset contains a hidden business problem: unprofitable sales in Southeast Asia due to excessive discounts

-- Drop tables if they exist to start fresh
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS regions CASCADE;

-- Create the Regions Table
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(255) NOT NULL,
    country VARCHAR(255) NOT NULL
);

-- Create the Customers Table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    segment VARCHAR(50) NOT NULL
);

-- Create the Products Table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sub_category VARCHAR(100) NOT NULL
);

-- Create the main Orders Table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id INT REFERENCES customers(customer_id),
    product_id INT REFERENCES products(product_id),
    region_id INT REFERENCES regions(region_id),
    sales DECIMAL(10, 2) NOT NULL,
    quantity INT NOT NULL,
    discount DECIMAL(3, 2) NOT NULL,
    profit DECIMAL(10, 2) NOT NULL
);

-- Insert Data into Regions
INSERT INTO regions (region_id, region_name, country) VALUES
(1, 'Southeast Asia', 'Malaysia'),
(2, 'Southeast Asia', 'Singapore'),
(3, 'North America', 'United States'),
(4, 'Europe', 'Germany');

-- Insert Data into Customers
INSERT INTO customers (customer_id, customer_name, segment) VALUES
(1, 'Bryan Lee', 'Consumer'),
(2, 'Venture Corp', 'Corporate'),
(3, 'Anna Smith', 'Home Office'),
(4, 'Global Tech Inc', 'Corporate');

-- Insert Data into Products
INSERT INTO products (product_id, product_name, category, sub_category) VALUES
(1, 'Executive Leather Chair', 'Furniture', 'Chairs'),
(2, 'Conference Table', 'Furniture', 'Tables'),
(3, 'Pine Bookcase', 'Furniture', 'Bookcases'),
(4, 'Galaxy S25', 'Technology', 'Phones'),
(5, 'QuantumBook Pro', 'Technology', 'Laptops'),
(6, 'Smart Toaster Oven', 'Appliances', 'Kitchen'),
(7, 'Eco-Friendly Binders', 'Office Supplies', 'Binders');

-- Insert Order Data (Engineered for the Demo Story)
-- NOTE: The story is hidden in here. Tables in SEA have high sales but NEGATIVE profit due to high discounts.
INSERT INTO orders (order_date, customer_id, product_id, region_id, sales, quantity, discount, profit) VALUES
-- Profitable Sales (The Control Group)
('2024-10-05', 1, 4, 3, 1200.00, 2, 0.00, 480.00),  -- Phones in North America, no discount, high profit
('2024-11-12', 2, 5, 4, 3000.00, 2, 0.10, 900.00),  -- Laptops in Europe, small discount, good profit
('2024-11-20', 1, 1, 1, 600.00, 2, 0.10, 150.00),   -- Chairs in SEA, profitable

-- *** THE HIDDEN PROBLEM: UNPROFITABLE BEST-SELLERS IN SOUTHEAST ASIA ***
('2024-09-15', 2, 2, 1, 1800.00, 3, 0.50, -550.00), -- Tables in Malaysia, high sales, HUGE discount, BIG loss
('2024-10-22', 4, 2, 2, 1200.00, 2, 0.50, -380.00), -- Tables in Singapore, high sales, HUGE discount, BIG loss
('2024-08-01', 3, 3, 1, 800.00, 4, 0.60, -210.00),   -- Bookcases in Malaysia, high sales, HUGE discount, loss
('2024-11-30', 4, 6, 2, 450.00, 3, 0.40, -80.00),    -- Appliances in Singapore, decent sales, high discount, loss

-- More filler data to make it look real
('2025-01-20', 3, 7, 3, 50.00, 10, 0.00, 20.00),   -- Office Supplies in NA, profitable
('2025-02-10', 2, 1, 4, 900.00, 3, 0.10, 220.00),   -- Chairs in Europe, profitable
('2025-03-14', 1, 5, 1, 1500.00, 1, 0.15, 350.00),  -- Laptop in SEA, profitable
('2025-04-01', 4, 4, 2, 650.00, 1, 0.00, 250.00);    -- Phone in Singapore, profitable

-- Verify the data
SELECT 'Data loaded successfully!' as status;
SELECT COUNT(*) as total_orders FROM orders;
SELECT COUNT(*) as total_products FROM products;
SELECT COUNT(*) as total_customers FROM customers;
SELECT COUNT(*) as total_regions FROM regions;
```

```scripts/setup_dataset.py
#!/usr/bin/env python3
"""
CogniQuery Dataset Setup Script
Helps users easily set up the sample e-commerce dataset for demo purposes.
"""

import os
import psycopg2
from dotenv import load_dotenv

def setup_sample_data():
    """Set up the sample dataset in the configured database."""
    print("🤖 CogniQuery Dataset Setup")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Get database connection string
    db_conn_str = os.getenv("NEONDB_CONN_STR")
    
    if not db_conn_str:
        print("❌ Error: NEONDB_CONN_STR not found in environment variables.")
        print("Please set up your .env file with your database connection string.")
        return False
    
    # Read the SQL script
    script_path = os.path.join(os.path.dirname(__file__), "dataset.sql")
    
    if not os.path.exists(script_path):
        print(f"❌ Error: SQL script not found at {script_path}")
        return False
    
    try:
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        print(f"📖 Found SQL script: {script_path}")
        print(f"📊 Script size: {len(sql_script)} characters")
        
        # Connect to database
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(db_conn_str)
        cursor = conn.cursor()
        
        # Execute the SQL script
        print("🚀 Executing SQL script...")
        cursor.execute(sql_script)
        conn.commit()
        
        # Verify the data was loaded
        print("✅ Verifying data setup...")
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM regions")
        region_count = cursor.fetchone()[0]
        
        print(f"📊 Data loaded successfully!")
        print(f"   - {order_count} orders")
        print(f"   - {product_count} products")
        print(f"   - {customer_count} customers")
        print(f"   - {region_count} regions")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Sample dataset setup complete!")
        print("\n💡 Try these sample queries in CogniQuery:")
        print("   • 'Our profit in Southeast Asia is a disaster. Find the top 3 sub-categories that are losing the most money in that region.'")
        print("   • 'Show me the relationship between discount levels and profitability.'")
        print("   • 'Which customer segment is most profitable and why?'")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_sample_data()
    if not success:
        print("\n❌ Setup failed. Please check your database connection and try again.")
        exit(1)
    else:
        print("\n✅ You're ready to use CogniQuery! Run 'streamlit run app.py' to get started.")
```

```src/cogniquery_crew/crew.py
# src/cogniquery_crew/crew.py

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.schema_explorer_tool import SchemaExplorerTool
from .tools.local_code_executor import LocalCodeExecutorTool
from .tools.sample_data_tool import SampleDataTool
from .tools.sql_executor_tool import SQLExecutorTool
from .tools.reporting_tools import ReportingTools
from .tools.activity_logger import get_activity_logger

# Set up the default LLM
os.environ["OPENAI_MODEL_NAME"] = "gpt-4.1"

# Base directory for configuration files
BASE_DIR = os.path.dirname(__file__)

@CrewBase
class CogniQueryCrew():
    """CogniQuery crew for data analysis and reporting."""
    # Configuration file paths
    agents_config = os.path.join(BASE_DIR, 'config', 'agents.yaml')
    tasks_config = os.path.join(BASE_DIR, 'config', 'tasks.yaml')

    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.schema_tool = SchemaExplorerTool()
        self.sample_data_tool = SampleDataTool()
        self.sql_executor_tool = SQLExecutorTool()
        self.report_tool = ReportingTools()
        self.local_code_executor = LocalCodeExecutorTool()
        
        # Configure all database tools with the connection string
        for tool in [self.schema_tool, self.sample_data_tool, self.sql_executor_tool]:
            if hasattr(tool, 'db_connection_string'):
                tool.db_connection_string = db_connection_string
        
        # Clear previous activity log
        logger = get_activity_logger()
        logger.clear_log()

    @agent
    def prompt_enhancer(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_enhancer'],
            tools=[self.schema_tool, self.sample_data_tool],
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[self.schema_tool, self.sample_data_tool, self.sql_executor_tool, self.local_code_executor],
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'],
            verbose=True
        )

    @task
    def enhance_prompt_task(self) -> Task:
        logger = get_activity_logger()
        task_config = self.tasks_config['enhance_prompt_task']
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Business Analyst", "enhance_prompt_task", task_config['description'])
        
        return Task(
            config=task_config,
            agent=self.prompt_enhancer(),
            callbacks={'on_start': log_start_callback}
        )

    @task
    def analyze_data_task(self) -> Task:
        logger = get_activity_logger()
        # Notify agent that connection is auto-configured
        task_description = self.tasks_config['analyze_data_task']['description'] + "\n\nNOTE: The database connection is automatically configured. When using Database Tools, only provide the SQL query."
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Data Scientist", "analyze_data_task", task_description)
        
        return Task(
            config={
                'description': task_description,
                'expected_output': self.tasks_config['analyze_data_task']['expected_output']
            },
            agent=self.data_analyst(),
            context=[self.enhance_prompt_task()],  # Direct dependency on business analyst
            callbacks={'on_start': log_start_callback}
        )

    @task
    def generate_report_task(self) -> Task:
        logger = get_activity_logger()
        # Write the final markdown report to a file for later PDF conversion
        md_path = "output/final_report.md"
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Communications Strategist", "generate_report_task", self.tasks_config['generate_report_task']['description'])
        
        return Task(
            config=self.tasks_config['generate_report_task'],
            agent=self.report_generator(),
            context=[self.analyze_data_task()],
            output_file=md_path,
            callbacks={'on_start': log_start_callback}
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CogniQuery crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
```

```src/cogniquery_crew/config/agents.yaml
# src/cogniquery_crew/config/agents.yaml

prompt_enhancer:
  role: >
    Senior Business Intelligence Analyst & Data Strategy Consultant
  goal: >
    Transform vague user queries into highly detailed, actionable analytical requirements by conducting 
    comprehensive database schema exploration and feasibility assessment. Your refined questions should 
    be so precise that they eliminate ambiguity and guide the entire analysis pipeline effectively.
    You must ensure every refined query leverages the full potential of available data structures and 
    anticipates downstream analytical needs.
  backstory: >
    You are a world-class business intelligence analyst with 15+ years of experience translating 
    executive-level business questions into data-driven insights. You possess an exceptional ability 
    to see the bigger picture while maintaining attention to granular details. Your expertise spans 
    across industries, and you understand that great analysis starts with great questions.
    
    STRATEGIC APPROACH:
    1. Always begin with comprehensive schema exploration to understand data relationships, constraints, and opportunities
    2. Use the Database Tools to examine table relationships, primary keys, and foreign keys
    3. Consider temporal aspects (time-based analysis), dimensional breakdowns, and comparative metrics
    4. Anticipate follow-up questions executives might ask and ensure your refined query enables those insights
    5. Think about data quality, sample sizes, and statistical significance when crafting requirements
    6. Consider multiple analytical angles: trends, comparisons, distributions, correlations, and outliers
    7. Examine sample data from key tables to understand data patterns and quality
    
    DATABASE EXPLORATION METHODOLOGY:
    - Use SchemaExplorer() to understand table structure and relationships
    - Identify primary keys, foreign keys, and table relationships
    - Use SampleData(table_name='table_name') to examine actual data content and quality
    - Look for date/time columns that enable temporal analysis
    - Understand dimensional hierarchies and categorical breakdowns
    - Identify potential data quality issues or missing values
    
    QUALITY STANDARDS:
    - Your refined questions should be executable without further clarification
    - Include specific metrics, dimensions, filters, and time periods
    - Specify the business context and expected decision-making impact
    - Ensure the question can support both summary insights and detailed drill-downs
    
    COMMON PITFALLS TO AVOID:
    - Vague metrics without clear calculation methods
    - Ignoring data relationships and foreign keys
    - Questions that can't leverage available dimensional data
    - Requirements that ignore business seasonality or cyclical patterns
    - Analysis scope too narrow to provide actionable insights

data_analyst:
  role: >
    Principal Data Scientist, SQL Expert & Advanced Analytics Expert - CHART CREATION SPECIALIST
  goal: >
    Execute SQL queries AND create visualizations for every analysis. You MUST use both SQLExecutor 
    and Code Interpreter tools for every task. Your primary responsibility is creating charts that 
    communicate insights effectively.
  backstory: >
    You are a renowned data scientist who NEVER performs analysis without creating visualizations.
    You understand that data without charts is incomplete analysis. You have a strict workflow:
    1. Execute SQL query with SQLExecutor
    2. IMMEDIATELY create charts with Code Interpreter  
    3. Provide analysis with chart references
    
    🚨 MANDATORY TOOL USAGE SEQUENCE:
    1. SQLExecutor(sql_query="your_query") - Get data from database
    2. Code Interpreter(code="your_python_code") - Create charts IMMEDIATELY after SQL
    3. Provide markdown analysis referencing the charts
    
    🚨 CRITICAL RULE: After EVERY SQLExecutor call, you MUST call Code Interpreter
    🚨 NO EXCEPTIONS: Charts are required for every analysis
    🚨 If you don't use Code Interpreter, NO CHARTS will appear in the UI
    
    TOOL CALLING EXAMPLES:
    ✅ CORRECT: SQLExecutor(sql_query="SELECT profit, discount FROM orders") → Code Interpreter(code="import pandas as pd...", libraries_used=['pandas', 'matplotlib', 'numpy'])
    ❌ WRONG: Only using SQLExecutor without Code Interpreter
    ❌ WRONG: Claiming to create charts without calling Code Interpreter
    ❌ WRONG: Using "LocalCodeExecutor" (tool doesn't exist - use Code Interpreter)
    ❌ WRONG: Missing libraries_used parameter in Code Interpreter calls
    
    VERIFICATION REQUIREMENT:
    - You must ACTUALLY call tools, not just describe what you would do
    - Real tool calls will appear in the activity log
    - If Code Interpreter isn't called, NO charts will be created
    - Never claim charts exist unless you actually called Code Interpreter
    
    SQL EXPERTISE:
    - Master of PostgreSQL, MySQL, and other major database engines
    - CURRENTLY WORKING WITH: NeonDB PostgreSQL database
    - Expert in PostgreSQL-specific syntax, functions, and optimization
    - Skilled in complex joins, window functions, CTEs, and advanced PostgreSQL patterns
    - Experienced with PostgreSQL statistical functions and percentile calculations
    - Always validate schema details and optimize for PostgreSQL specifically
    - CRITICAL: Use single quotes for string literals in WHERE clauses: WHERE region_name = 'Southeast Asia'
    - CRITICAL: Use proper PostgreSQL syntax and functions (STRING_AGG, COALESCE, etc.)
    - CRITICAL: PostgreSQL is case-sensitive for quoted identifiers
    
    QUERY CONSTRUCTION METHODOLOGY:
    - Start with the most selective filters to reduce data volume early
    - Use EXISTS instead of IN for subqueries when appropriate
    - Leverage PostgreSQL window functions for complex analytical calculations
    - Implement proper GROUP BY and aggregate function usage
    - Use CASE statements for conditional logic and data transformation
    - Apply proper date/time handling for temporal analysis using PostgreSQL functions
    - Handle edge cases like NULL values, division by zero, and empty result sets
    - CRITICAL POSTGRESQL SYNTAX RULES:
      * Use single quotes for string literals: WHERE region_name = 'Southeast Asia'
      * Use double quotes for column names with spaces: SELECT "column name"
      * PostgreSQL is case-sensitive for quoted identifiers
      * Always test queries with sample data first
      * Use proper JOIN syntax: LEFT JOIN, INNER JOIN, etc.
      * Handle multi-word values properly: 'North America', 'Southeast Asia'
      * Use PostgreSQL-specific functions when appropriate: STRING_AGG(), COALESCE(), etc.
    
    ANALYTICAL METHODOLOGY:
    1. Data Quality Assessment: Always validate data integrity, check for outliers, missing values, and inconsistencies
    2. Exploratory Data Analysis: Understand distributions, correlations, and patterns before formal analysis
    3. Statistical Validation: Apply appropriate statistical tests and confidence intervals to findings
    4. Comparative Analysis: Benchmark against industry standards, historical trends, or peer groups when possible
    5. Predictive Insights: Where appropriate, identify trends and provide forward-looking projections
    6. Actionable Recommendations: Connect every insight to specific business actions or decisions
    
    VISUALIZATION EXCELLENCE STANDARDS:
    - CRITICAL: ALWAYS use Code Interpreter tool to create charts - this is MANDATORY
    - CRITICAL: ALWAYS use plt.savefig() to save charts - this is the ONLY way charts are displayed
    - Create STUNNING, ENGAGING charts that tell compelling visual stories
    - Use descriptive filenames: 'output/chart_1.png', 'output/chart_2.png', etc.
    - For single charts, use: plt.savefig('output/chart.png') 
    - For multiple charts, use: plt.savefig('output/chart_1.png'), plt.savefig('output/chart_2.png')
    
    🎨 ADVANCED VISUAL DESIGN REQUIREMENTS:
    - Use BEAUTIFUL color palettes: gradients, custom colors, professional themes
    - Apply sophisticated styling: custom fonts, elegant backgrounds, modern aesthetics
    - Create MULTIPLE chart types for same data: bar charts, line plots, area charts, scatter plots
    - Add visual enhancements: shadows, transparency, gradients, custom markers
    - Include data annotations: value labels, trend lines, statistical markers
    - Use advanced matplotlib features: subplots, secondary axes, insets, annotations
    - Apply executive-quality formatting: clean grids, professional typography, branded colors
    
    📊 CHART TYPE DIVERSITY & CREATIVITY:
    - Bar Charts: Use gradient colors, custom widths, horizontal/vertical orientations
    - Line Charts: Add markers, fill areas, multiple series with different styles
    - Scatter Plots: Vary point sizes, colors by category, add trend lines
    - Area Charts: Use transparency, stacking, beautiful color fills
    - Combination Charts: Mix different chart types in same figure
    - Heatmaps: Use custom color scales, annotations, professional styling
    - Box Plots & Violin Plots: For distribution analysis with elegant styling
    
    🎯 PROFESSIONAL STYLING TECHNIQUES:
    - Use plt.style.use() for professional themes ('seaborn-v0_8', 'ggplot', custom styles)
    - Apply custom color palettes: ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'] or similar
    - Add subtle backgrounds: plt.gca().set_facecolor('#f8f9fa')
    - Use elegant fonts: plt.rcParams.update({'font.family': 'sans-serif'})
    - Apply transparency effects: alpha parameters for sophistication
    - Add grid styling: plt.grid(True, alpha=0.3, linestyle='--')
    - Include reference lines: plt.axhline(), plt.axvline() for context
    
    📈 DATA STORYTELLING ENHANCEMENTS:
    - Add detailed titles with insights: "Profit Margin Drops 65% Beyond 30% Discount Threshold"
    - Include subtitles explaining key findings
    - Use annotations to highlight critical data points
    - Add callout boxes for important insights
    - Include percentage changes, growth rates, statistical significance
    - Show trend directions with arrows or special markers
    - Use color coding to emphasize positive/negative performance
    
    🎪 ADVANCED MATPLOTLIB FEATURES TO USE:
    - plt.subplots() for multi-panel layouts
    - plt.text() and plt.annotate() for rich annotations
    - Custom legends with detailed explanations
    - Secondary y-axes for different metrics
    - Inset plots for detailed views
    - Custom color maps and gradients
    - 3D elements where appropriate (limited use)
    - Animation-ready layouts (static frames)
    
    - CRITICAL: All chart files in output/ directory will be displayed in the Streamlit UI
    - CRITICAL: Without plt.savefig(), no charts will appear in the UI
    - CRITICAL: When referencing charts in markdown, use relative paths (just 'chart_name.png') since markdown and images are in same directory
    - EXAMPLE: Code Interpreter(code='import matplotlib.pyplot as plt; plt.style.use("seaborn-v0_8"); fig, ax = plt.subplots(figsize=(12, 8)); ax.bar([1,2,3], [4,5,6], color=["#2E86AB", "#A23B72", "#F18F01"], alpha=0.8); plt.title("Stunning Chart Title", fontsize=16, fontweight="bold"); plt.savefig("output/chart_1.png", dpi=300, bbox_inches="tight"); plt.close()', libraries_used=['matplotlib', 'pandas', 'numpy'])
    
    CHART SAVING REQUIREMENTS:
    - MANDATORY: Every chart MUST be saved with plt.savefig('output/filename.png')
    - MANDATORY: Use .png format for all charts
    - MANDATORY: Save charts to 'output/' directory
    - MANDATORY: Use plt.close() after saving each chart to clear memory
    - RECOMMENDED: Use plt.figure(figsize=(12, 8)) for larger, more detailed charts
    - RECOMMENDED: Use high DPI for crisp quality: dpi=300, bbox_inches='tight'
    
    🎨 ENHANCED CHART CREATION PATTERN:
    ```python
    import matplotlib.pyplot as plt
    import numpy as np
    plt.style.use('seaborn-v0_8')  # Professional styling
    
    fig, ax = plt.subplots(figsize=(12, 8))
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3D5A80']
    
    # Create stunning visualizations with:
    # - Custom colors and gradients
    # - Detailed annotations
    # - Professional typography
    # - Statistical insights overlaid
    # - Multiple data representations
    
    plt.title('Compelling Title with Key Insight', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Descriptive X Label', fontsize=14)
    plt.ylabel('Descriptive Y Label', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Add annotations, trend lines, reference points
    plt.savefig('output/chart_1.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    ```
    
    🚀 CREATIVE VISUALIZATION IDEAS:
    - Dual-axis charts showing multiple metrics
    - Annotated scatter plots with trend analysis
    - Stacked area charts with gradient fills
    - Multi-panel dashboard-style layouts
    - Before/after comparison charts
    - Performance threshold indicator lines
    - Color-coded performance zones (green/yellow/red)
    - Statistical confidence intervals
    - Interactive-style legends with detailed explanations
    
    TOOL USAGE REQUIREMENTS:
    - ALWAYS use SQLExecutor() first to get data from the database
    - ALWAYS use Code Interpreter() second to create charts and perform analysis
    - CRITICAL: Always include libraries_used parameter with Code Interpreter calls
    - Do NOT skip the Code Interpreter step - charts are required for every analysis
    - The Code Interpreter tool executes Python code and creates visualizations
    - Without Code Interpreter + plt.savefig(), no charts will be generated or displayed
    - MANDATORY: Use libraries_used=['pandas', 'matplotlib', 'numpy'] for all chart creation
    
    PYTHON/PANDAS BEST PRACTICES:
    - Always validate column existence before analysis: `if 'column_name' in df.columns:`
    - Handle missing data appropriately with explicit strategies
    - Use vectorized operations for performance optimization
    - Implement proper data type conversions and date handling
    - Create reusable functions for complex calculations
    - Add descriptive comments explaining analytical choices
    - ALWAYS use: import matplotlib.pyplot as plt
    - CRITICAL: ALWAYS use plt.savefig() to save every chart you create
    - For chart saving, use descriptive filenames: 'output/chart_1.png', 'output/chart_2.png', etc.
    - For single charts, you can still use: plt.savefig('output/chart.png')
    - MANDATORY: Use plt.close() after each plt.savefig() to clear matplotlib memory
    
    🎨 ADVANCED VISUALIZATION LIBRARIES & TECHNIQUES:
    - Use matplotlib's built-in styles: plt.style.use('seaborn-v0_8', 'ggplot', 'bmh')
    - Apply color theory: complementary colors, gradients, opacity effects
    - Create custom color palettes for brand consistency
    - Use matplotlib.patches for custom shapes and highlights
    - Apply matplotlib.animation concepts (for static frames)
    - Utilize subplots for comparative analysis dashboards
    - Add statistical overlays: trend lines, confidence bands, benchmarks
    
    🎯 CHART ENHANCEMENT REQUIREMENTS:
    - Every chart must have a compelling, insight-driven title
    - Include subtitles or annotations explaining key findings
    - Use professional color schemes (avoid default matplotlib colors)
    - Add value labels on data points where appropriate
    - Include reference lines, benchmarks, or performance thresholds
    - Apply consistent styling across all charts in same analysis
    - Use transparency and layering for sophisticated visual depth
    - Add context through background shading or color zones
    
    CRITICAL RESTRICTION: NEVER use 'import os' or any os module functions
    - Do NOT attempt to check file existence, directory contents, or file system operations
    - Trust that plt.savefig() will work correctly with any valid filename
    - Focus on creating STUNNING visualizations, not file management
    
    AVAILABLE LIBRARIES & RESTRICTIONS:
    - Core libraries available: pandas, numpy, matplotlib, datetime, json, re
    - Database connectivity: psycopg2, sqlalchemy (for PostgreSQL connections)
    - Statistical analysis: scipy.stats (basic statistical functions)
    - UNAVAILABLE libraries: tabulate, seaborn, plotly, bokeh, altair
    - For markdown tables: Use manual formatting instead of df.to_markdown()
    - Create markdown tables manually with proper formatting like:
      ```
      | Column 1 | Column 2 | Column 3 |
      |----------|----------|----------|
      | Value 1  | Value 2  | Value 3  |
      ```
    - Alternative to df.to_markdown(): Use string formatting or build tables manually
    - If you need tabulate functionality, create simple table formatting functions
    
    STATISTICAL RIGOR REQUIREMENTS:
    - Calculate and report confidence intervals for key metrics
    - Identify and explain any assumptions in your analysis
    - Test for statistical significance when making comparisons
    - Account for seasonality, trends, and cyclical patterns
    - Distinguish between correlation and causation
    - Provide context for the practical significance of findings
    
    STORYTELLING FRAMEWORK:
    - Executive Summary: Key findings that matter to decision makers
    - Supporting Evidence: Detailed analysis with statistical backing
    - Visual Narrative: Charts that reinforce and clarify insights
    - Implications: What this means for the business
    - Recommendations: Specific, actionable next steps
    - Future Analysis: Suggestions for deeper investigation
    
    COMMON PITFALLS TO AVOID:
    - Assuming columns exist without verification
    - Cherry-picking data to support preconceived notions
    - Ignoring outliers without investigation
    - Creating misleading visualizations
    - Failing to provide business context for statistical findings
    - Over-complicating analysis when simple insights suffice
    - Using unclear or non-descriptive chart filenames
    - Forgetting to import matplotlib.pyplot as plt
    
    QUALITY IMPROVEMENT PROCESS:
    - Review your analysis from multiple perspectives
    - Validate findings through alternative analytical approaches
    - Seek the simplest explanation that accounts for the data
    - Ensure reproducibility of all calculations and visualizations

report_generator:
  role: >
    Executive Communications Director & Strategic Storytelling Expert
  goal: >
    Transform complex analytical findings into compelling, executive-ready reports that drive decision-making 
    and strategic action. Your reports should seamlessly blend analytical rigor with clear business narrative, 
    making sophisticated insights accessible to C-suite executives while maintaining technical credibility. 
    Create documents that not only inform but inspire action and confidence in data-driven decisions.
    Alwasys include a tldr at the top.
  backstory: >
    You are a master communicator with an MBA from Wharton and 15+ years of experience crafting executive 
    communications for Fortune 100 companies. You've written board presentations, investor reports, and 
    strategic recommendations that influenced billion-dollar decisions. Your unique gift is translating 
    complex data science into compelling business narratives that resonate with senior leadership.
    
    EXECUTIVE COMMUNICATION PRINCIPLES:
    1. Lead with Impact: Start with the most important finding that drives business value
    2. SCQA Framework: Situation, Complication, Question, Answer for logical flow
    3. Pyramid Principle: Most important points first, supporting details follow
    4. So What Test: Every insight must answer "Why does this matter to our business?"
    5. Action Orientation: Connect every finding to specific decisions or next steps
    6. Risk Assessment: Acknowledge limitations and provide confidence levels
    
    REPORT STRUCTURE EXCELLENCE:
    - Executive Summary: 3-5 bullet points capturing the essence for time-constrained leaders
    - Strategic Context: Why this analysis matters now and how it fits broader business objectives
    - Key Findings: Prioritized insights with clear business implications
    - Supporting Evidence: Visual and analytical proof points that build credibility
    - Risk Considerations: Potential limitations, assumptions, and confidence levels
    - Strategic Recommendations: Specific, time-bound actions with expected outcomes
    - Implementation Roadmap: Clear next steps and resource requirements
    - Future Analytics: Suggested follow-up analyses to continue the insights journey
    
    VISUAL COMMUNICATION MASTERY:
    - Integrate charts seamlessly into narrative flow
    - Use executive-friendly color schemes (blues, grays, accent colors)
    - Ensure all visuals are self-explanatory with clear titles and annotations
    - Apply consistent formatting and professional typography
    - Include comparison benchmarks and context for all metrics
    - Highlight key data points that support strategic recommendations
    
    BUSINESS LANGUAGE OPTIMIZATION:
    - Replace statistical jargon with business terminology
    - Use active voice and confident assertions backed by data
    - Quantify impact in business terms (revenue, cost, efficiency, risk)
    - Frame findings as opportunities or threats requiring action
    - Include relevant industry context and competitive implications
    - Connect data insights to company strategic priorities
    
    CREDIBILITY BUILDING TECHNIQUES:
    - Cite data sources and methodology transparently
    - Acknowledge analytical limitations without undermining confidence
    - Provide confidence intervals and statistical significance where relevant
    - Include peer benchmarks or industry standards for context
    - Show sensitivity analysis for key assumptions
    - Demonstrate logical progression from data to conclusions
    
    EXECUTIVE DECISION-MAKING SUPPORT:
    - Present options with clear trade-offs and risk profiles
    - Include implementation complexity and resource requirements
    - Suggest pilot programs or phased approaches when appropriate
    - Identify key performance indicators to track success
    - Recommend monitoring and review cycles
    - Connect to broader strategic initiatives and OKRs
    
    REPORT QUALITY STANDARDS:
    - Every paragraph should advance the business narrative
    - Technical accuracy combined with business relevance
    - Logical flow from problem identification to solution recommendation
    - Professional formatting suitable for board-level distribution
    - Actionable insights that can be implemented within existing organizational capabilities
    - Future-forward perspective that anticipates evolving business needs
```

```src/cogniquery_crew/config/tasks.yaml
# src/cogniquery_crew/config/tasks.yaml

enhance_prompt_task:
  description: >
    Take the user's query: '{query}' and refine it into a single, highly detailed,
    and specific question that is ready for data analysis. First, examine the database
    schema using SchemaExplorer() to understand what tables, columns, data types,
    relationships, and constraints are available. Then examine sample data from key
    tables using SampleData(table_name='table_name') to understand data patterns. 
    Pay special attention to:
    
    1. Primary keys and foreign key relationships between tables
    2. Data types and constraints for each column
    3. Sample data from relevant tables to understand data quality and patterns
    4. Temporal columns that enable time-based analysis
    5. Categorical dimensions for breakdowns and comparisons
    
    Then refine the user's query to be specific about which data fields should be analyzed,
    how tables should be joined, and what relationships should be leveraged. Ensure the 
    question is feasible with the available data structure and takes advantage of the 
    relational database design.
    
    The question must be self-contained and unambiguous, providing clear guidance on:
    - Which tables to query and how they relate
    - What metrics to calculate and how
    - What dimensions to analyze
    - What time periods or filters to apply
  expected_output: >
    A single, refined, and detailed question in plain English that specifically references
    the available data fields, table relationships, and is feasible with the current database schema.
    Include context about how tables are related and what joins will be necessary.

analyze_data_task:
  description: >
    Based on the refined question from the Business Analyst, you MUST follow this EXACT workflow:
    
    STEP 1: Execute SQL Query
    - Use SQLExecutor(sql_query='your_query') to get data from the database
    
    STEP 2: IMMEDIATELY Use Code Interpreter (MANDATORY)
    - As soon as you get SQL results, you MUST call Code Interpreter(code='your_python_code')
    - Extract the CSV data from the SQL results
    - Create STUNNING, DETAILED charts using matplotlib.pyplot
    - Apply professional styling, custom colors, and engaging visual design
    - Save charts with plt.savefig('output/chart_1.png')
    
    STEP 3: Provide Analysis
    - Summarize findings in markdown format
    - Reference the charts you created
    
    CRITICAL REQUIREMENTS:
    🚨 YOU MUST CALL BOTH SQLExecutor AND Code Interpreter TOOLS 
    🚨 NO EXCEPTIONS - Code Interpreter is REQUIRED after every SQL query
    🚨 Charts MUST be created and saved to output/ directory
    🚨 If you don't use Code Interpreter, NO CHARTS will appear in the UI
    
    WORKFLOW ENFORCEMENT:
    - Database: NeonDB PostgreSQL - use proper PostgreSQL syntax
    - After SQLExecutor returns results, IMMEDIATELY call Code Interpreter
    - Use this exact pattern:
      1. SQLExecutor(sql_query="SELECT * FROM table")
      2. Code Interpreter(code="import pandas as pd; import matplotlib.pyplot as plt; # create charts", libraries_used=['pandas', 'matplotlib', 'numpy'])
    
    MANDATORY CODE INTERPRETER USAGE:
    After getting CSV data from SQLExecutor, you must immediately call:
    Code Interpreter(code='''
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np
    import io

    # Apply professional styling
    plt.style.use('seaborn-v0_8')
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3D5A80']

    # Extract CSV data from SQL results (remove instruction text)
    csv_data = """[PASTE CLEAN CSV DATA HERE]"""
    df = pd.read_csv(io.StringIO(csv_data))

    # Create STUNNING visualizations with multiple approaches
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Use advanced matplotlib features:
    # - Custom colors and gradients
    # - Detailed annotations with insights
    # - Professional typography and styling
    # - Statistical overlays and trend analysis
    # - Multiple chart types and combinations
    
    plt.title('Compelling Title with Key Business Insight', fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('Descriptive X-Axis Label', fontsize=14)
    plt.ylabel('Descriptive Y-Axis Label', fontsize=14)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Add annotations, trend lines, statistical insights
    plt.savefig('output/chart_1.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
        ''', libraries_used=['pandas', 'matplotlib', 'numpy'])
    CRITICAL plt.savefig() REQUIREMENTS:
    - MANDATORY: Every chart must be saved with plt.savefig('output/filename.png')
    - MANDATORY: Use .png format only
    - MANDATORY: Save to 'output/' directory
    - MANDATORY: Use plt.close() after each plt.savefig()
    - RECOMMENDED: Use dpi=300 and bbox_inches='tight' for high quality
    - Without plt.savefig(), charts will NOT appear in the Streamlit UI
    
    PYTHON CODE STRUCTURE:
    1. Import required libraries (pandas, matplotlib.pyplot, numpy)
    2. Write and execute the SQL query to get data
    3. Process the data from SQL results
    4. Create your analysis and calculations  
    5. Generate MULTIPLE stunning, professional charts with:
       - Custom color palettes and professional styling
       - Detailed annotations and insights overlaid
       - Advanced matplotlib features (subplots, annotations, etc.)
       - Executive-quality formatting and typography
       - Statistical enhancements (trend lines, benchmarks, etc.)
    6. Save charts using descriptive filenames (chart_1.png, chart_2.png, etc.)
    7. Create a markdown table manually (do NOT use df.to_markdown() - tabulate is unavailable)
    
    CHART NAMING CONVENTIONS:
    - Single chart: 'output/chart.png' OR 'output/chart_1.png' 
    - Multiple charts: 'output/chart_1.png', 'output/chart_2.png', 'output/chart_3.png', etc.
    - Use descriptive names if helpful: 'output/sales_trend.png', 'output/category_breakdown.png'
    - All PNG files in output/ directory will be automatically displayed
    
    MARKDOWN TABLE FORMATTING:
    - Create tables manually using this format:
      | Column 1 | Column 2 | Column 3 |
      |----------|----------|----------|
      | Value 1  | Value 2  | Value 3  |
    - Use proper alignment and spacing
    - Include all relevant data from your analysis
    - Format numbers appropriately (2 decimal places for currency, etc.)
    
    IMPORTANT RESTRICTIONS:
    - Do NOT use 'import os' or any os module functions
    - Do NOT use df.to_markdown() - tabulate library is unavailable
    - Do NOT try to check file existence or directory contents
    - Simply save charts with plt.savefig() and trust it works
    - Focus on creating great visualizations, not file system operations
    - Available libraries: pandas, numpy, matplotlib, datetime, json, re, psycopg2, sqlalchemy
    - Unavailable libraries: tabulate, seaborn, plotly, bokeh, altair
    
    Your final output must be a markdown-formatted text containing:
    1. A summary of your key findings
    2. The data you analyzed, presented in a markdown table
    3. Reference to the charts created (e.g., "Charts saved as chart_1.png and chart_2.png")
    4. CONFIRMATION that charts were actually created using Code Interpreter
    5. When referencing charts in markdown text, use just filename (e.g., chart_1.png) since markdown and images are in same output/ directory
  expected_output: >
    A comprehensive analysis in markdown format, including a summary, a markdown table
    of the data, confirmation of which charts were created, and evidence that Code Interpreter was used for chart generation (e.g., "Charts saved as chart_1.png and chart_2.png").

generate_report_task:
  description: >
    Take the markdown-formatted analysis and insights and compile them into a final,
    professional report.
  expected_output: >
    A confirmation message that the PDF report has been successfully created.
```

```src/cogniquery_crew/tools/activity_logger.py
# src/cogniquery_crew/tools/activity_logger.py

import os
import json
import datetime
from typing import List, Dict, Any
import threading

class ActivityLogger:
    """Thread-safe activity logger for tracking agent activities and SQL queries."""
    
    def __init__(self, log_file_path: str = "output/activity_log.json"):
        self.log_file_path = log_file_path
        self.activities: List[Dict[str, Any]] = []
        self.current_agent: str = None
        self.current_task: str = None
        self._lock = threading.Lock()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Initialize log file
        self._save_to_file()
    
    def log_activity(self, agent_name: str, activity_type: str, content: str, details: Dict[str, Any] = None):
        """Log an activity with timestamp."""
        with self._lock:
            activity = {
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": agent_name,
                "type": activity_type,
                "content": content,
                "details": details or {}
            }
            self.activities.append(activity)
            self._save_to_file()
    
    def log_sql_query(self, agent_name: str, sql_query: str, result_preview: str = None):
        """Log an SQL query execution."""
        details = {}
        if result_preview:
            details["result_preview"] = result_preview[:500] + "..." if len(result_preview) > 500 else result_preview
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="sql_query",
            content=sql_query,
            details=details
        )
    
    def log_task_start(self, agent_name: str, task_name: str, description: str):
        """Log the start of a task."""
        with self._lock:
            self.current_agent = agent_name
            self.current_task = task_name
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="task_start",
            content=f"Starting task: {task_name}",
            details={"task_name": task_name, "description": description}
        )
    
    def log_task_complete(self, agent_name: str, task_name: str, output: str):
        """Log the completion of a task."""
        with self._lock:
            if self.current_task == task_name:
                self.current_agent = None
                self.current_task = None
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="task_complete",
            content=f"Completed task: {task_name}",
            details={"task_name": task_name, "output": output[:200] + "..." if len(output) > 200 else output}
        )
    
    def log_tool_usage(self, agent_name: str, tool_name: str, action: str, result: str = None):
        """Log tool usage."""
        details = {"tool_name": tool_name, "action": action}
        if result:
            details["result"] = result[:200] + "..." if len(result) > 200 else result
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="tool_usage",
            content=f"Used {tool_name}: {action}",
            details=details
        )
    
    def get_current_status(self) -> Dict[str, str]:
        """Get the current agent and task status."""
        with self._lock:
            return {
                "current_agent": self.current_agent,
                "current_task": self.current_task
            }
    
    def get_activities(self) -> List[Dict[str, Any]]:
        """Get all logged activities."""
        with self._lock:
            return self.activities.copy()
    
    def clear_log(self):
        """Clear all activities."""
        with self._lock:
            self.activities = []
            self.current_agent = None
            self.current_task = None
            self._save_to_file()
    
    def _save_to_file(self):
        """Save activities to JSON file."""
        try:
            with open(self.log_file_path, 'w') as f:
                json.dump(self.activities, f, indent=2)
        except Exception as e:
            print(f"Error saving activity log: {e}")

# Global logger instance
_logger_instance = None

def get_activity_logger() -> ActivityLogger:
    """Get the global activity logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ActivityLogger()
    return _logger_instance
```

```src/cogniquery_crew/tools/db_tools.py
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
```

```src/cogniquery_crew/tools/local_code_executor.py
# src/cogniquery_crew/tools/local_code_executor.py

import os
import sys
import subprocess
import tempfile
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class LocalCodeExecutorTool(BaseTool):
    """Local code executor tool that runs Python code in the current environment.
    
    This tool executes Python code locally instead of in a Docker container,
    ensuring access to all installed packages like matplotlib.
    """
    
    name: str = "LocalCodeExecutor"
    description: str = """MANDATORY: Execute Python code for data analysis and chart creation after EVERY SQL query.
    
    ⚠️  CRITICAL REQUIREMENT: This tool MUST be used to create charts and perform data analysis with Python.
    ⚠️  WITHOUT THIS TOOL, NO CHARTS WILL BE GENERATED OR DISPLAYED IN THE UI.
    
    WORKFLOW REQUIREMENT:
    1. Get data with SQLExecutor
    2. IMMEDIATELY use LocalCodeExecutor to create charts with that data
    3. Save charts with plt.savefig() - this is the ONLY way charts appear in the UI
    
    Parameters:
    - code: Python code to execute (required)
    
    CHART REQUIREMENTS (MANDATORY):
    - Use matplotlib.pyplot for visualizations: import matplotlib.pyplot as plt
    - Save charts to output directory: plt.savefig('output/chart_1.png')
    - Create as many charts as needed for comprehensive analysis
    - Charts are automatically displayed in the Streamlit UI ONLY if saved with plt.savefig()
    
    DATA INPUT PATTERN:
    - SQL results are typically provided as CSV strings
    - Use pd.read_csv(io.StringIO(csv_data)) to convert CSV strings to DataFrames
    - Always validate data before creating charts
    
    AVAILABLE LIBRARIES: pandas, numpy, matplotlib, datetime, json, re, io
    
    ⚠️  REMINDER: Without LocalCodeExecutor + plt.savefig(), NO CHARTS will appear in the UI!"""
    
    def __init__(self):
        super().__init__()
        
    def _run(self, code: str = None, **kwargs) -> str:
        """Run Python code locally and log the execution."""
        # Add debugging
        print(f"🐛 DEBUG: LocalCodeExecutor._run called with code={code is not None}, kwargs: {list(kwargs.keys())}")
        # Handle both calling patterns
        if code is None:
            code = kwargs.get('code', '')
        return self._execute_code(code=code, **kwargs)
    
    def run(self, **kwargs) -> str:
        """Alternative method name that some CrewAI versions might use."""
        print(f"🐛 DEBUG: LocalCodeExecutor.run called with kwargs: {list(kwargs.keys())}")
        return self._execute_code(**kwargs)
    
    def execute(self, **kwargs) -> str:
        """Another alternative method name."""
        print(f"🐛 DEBUG: LocalCodeExecutor.execute called with kwargs: {list(kwargs.keys())}")
        return self._execute_code(**kwargs)
    
    def _execute_code(self, code: str = None, **kwargs) -> str:
        """The actual implementation - all methods delegate to this."""
        # Add debugging
        print(f"🐛 DEBUG: LocalCodeExecutor._execute_code called with code={code is not None}, kwargs: {list(kwargs.keys())}")
        
        logger = get_activity_logger()
        
        # Extract code from kwargs if not provided directly
        if not code:
            code = kwargs.get('code', '')
        if not code:
            print("🐛 DEBUG: No code provided to LocalCodeExecutor")
            return "Error: No code provided to execute"
        
        print(f"🐛 DEBUG: Code to execute: {code[:100]}...")
        
        libraries_used = kwargs.get('libraries_used', [])
        
        # Check for problematic library usage and provide helpful guidance
        code = self._check_and_fix_common_issues(code)
        
        # Enhance code with reliable chart generation setup
        if 'plt.savefig' in code and 'output/' in code:
            # Inject reliable chart generation code
            enhanced_code = self._enhance_chart_code(code)
            code = enhanced_code
            print("🐛 DEBUG: Enhanced code with chart generation setup")
        
        # Avoid logging duplicate code executions
        if not hasattr(LocalCodeExecutorTool, '_last_logged_code'):
            LocalCodeExecutorTool._last_logged_code = None
            
        # Always log LocalCodeExecutor usage for debugging
        details = {"tool": "LocalCodeExecutor"}
        if libraries_used:
            details["libraries"] = libraries_used
            
        print("🐛 DEBUG: About to log activity...")
        logger.log_activity(
            agent_name="Data Scientist",
            activity_type="python_code",
            content=code[:500] + "..." if len(code) > 500 else code,
            details=details
        )
        print("🐛 DEBUG: Activity logged successfully")
        
        LocalCodeExecutorTool._last_logged_code = code
        
        # Execute code locally
        try:
            print("🐛 DEBUG: About to execute code locally...")
            result = self._execute_locally(code)
            print(f"🐛 DEBUG: Code execution result: {result[:200]}...")
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            print(f"🐛 DEBUG: Error executing code: {e}")
            logger.log_activity(
                agent_name="Data Scientist",
                activity_type="python_code",
                content=f"ERROR: {error_msg}",
                details={"error": str(e)}
            )
            return error_msg
        
        # Execute code locally
        try:
            result = self._execute_locally(code)
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            logger.log_activity(
                agent_name="Data Scientist",
                activity_type="python_code",
                content=f"ERROR: {error_msg}",
                details={"error": str(e)}
            )
            return error_msg

    def _execute_locally(self, code: str) -> str:
        """Execute Python code in the local environment."""
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code using the current Python interpreter
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.getcwd(),
                timeout=30,  # 30 second timeout
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}  # Force UTF-8 encoding
            )
            
            if result.returncode == 0:
                output = result.stdout
                if result.stderr:
                    output += f"\\nWarnings: {result.stderr}"
                
                # Check if any chart files were created
                chart_files = []
                if os.path.exists("output"):
                    for file in os.listdir("output"):
                        if file.endswith('.png'):
                            chart_files.append(file)
                
                if chart_files:
                    output += f"\\n\\nCharts created: {', '.join(chart_files)}"
                else:
                    output += "\\n\\nNo chart files were created in output directory"
                    
                return output or "Code executed successfully (no output)"
            else:
                error_output = f"Code execution failed:\\nReturn code: {result.returncode}\\nStdout: {result.stdout}\\nStderr: {result.stderr}"
                return error_output
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def _check_and_fix_common_issues(self, code: str) -> str:
        """Check for common issues and provide fixes or alternatives."""
        
        # Check for df.to_markdown() usage which requires tabulate
        if 'to_markdown(' in code:
            replacement_code = code.replace('df.to_markdown()', 'df.to_string()')
            return replacement_code
        
        # Check for other problematic imports
        problematic_imports = [
            ('import seaborn', 'seaborn is not available. Use matplotlib instead.'),
            ('import plotly', 'plotly is not available. Use matplotlib instead.'),
            ('import bokeh', 'bokeh is not available. Use matplotlib instead.'),
            ('import altair', 'altair is not available. Use matplotlib instead.'),
            ('from tabulate', 'tabulate is not available. Use manual table formatting.'),
        ]
        
        for problematic, suggestion in problematic_imports:
            if problematic in code:
                return f"# Error: {suggestion}\\n# Please rewrite your code without {problematic.split()[1]}\\n{code}"
        
        return code

    def _enhance_chart_code(self, original_code: str) -> str:
        """Enhance code to ensure reliable chart generation."""
        enhancement_prefix = '''
# === CHART GENERATION RELIABILITY ENHANCEMENTS ===
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import io
import os

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Clear any existing matplotlib state
plt.clf()
plt.close('all')

'''
        
        enhancement_suffix = '''

# === CHART SAVING WITH VERIFICATION ===
print("Chart generation code completed")

'''
        
        return enhancement_prefix + original_code + enhancement_suffix
```

```src/cogniquery_crew/tools/reporting_tools.py
# src/cogniquery_crew/tools/reporting_tools.py

import os
import base64
from crewai.tools import BaseTool
from markdown_it import MarkdownIt
from .activity_logger import get_activity_logger

class ReportingTools(BaseTool):
    name: str = "Reporting Tools"
    description: str = "A tool to create a PDF report from markdown content."

    def create_report(self, markdown_content: str, report_file_path: str) -> str:
        """
        Converts markdown content, including images and tables, into a PDF report.
        It saves the report to the specified file path.
        """
        logger = get_activity_logger()
        logger.log_tool_usage("Communications Strategist", "Reporting Tools", f"Creating PDF report at {report_file_path}")
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(report_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Convert markdown to HTML
        md = MarkdownIt()
        html_content = md.render(markdown_content)

        # Import WeasyPrint here to catch missing native dependencies
        try:
            from weasyprint import HTML, CSS
        except (ImportError, OSError) as e:
            error_msg = f"WeasyPrint import error: {e}. Please install WeasyPrint and its native dependencies as per https://doc.courtbouillon.org/weasyprint/stable/first_steps.html."
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", f"PDF creation failed: {error_msg}")
            return error_msg

        # Basic CSS for styling
        css = CSS(string='''
            @page { size: A4; margin: 2cm; }
            body { font-family: sans-serif; line-height: 1.5; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            img { max-width: 100%; height: auto; display: block; margin: 1em 0; }
        ''')

        # Create PDF
        try:
            HTML(string=html_content).write_pdf(report_file_path, stylesheets=[css])
            success_msg = f"Successfully created report at {report_file_path}"
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", success_msg)
            return success_msg
        except Exception as e:
            error_msg = f"Error creating PDF report: {e}"
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", error_msg)
            return error_msg

    def _run(self, markdown_content: str, report_file_path: str = None, **kwargs) -> str:
        """
        Abstract method implementation for BaseTool. Calls create_report.
        """
        # Get report file path from kwargs if not provided directly
        if not report_file_path and 'report_file_path' in kwargs:
            report_file_path = kwargs['report_file_path']
        
        if not report_file_path:
            return "Error: No report file path provided"
            
        return self.create_report(markdown_content, report_file_path)
```

```src/cogniquery_crew/tools/sample_data_tool.py
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
```

```src/cogniquery_crew/tools/schema_explorer_tool.py
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
```

```src/cogniquery_crew/tools/sql_executor_tool.py
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
```

