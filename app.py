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
