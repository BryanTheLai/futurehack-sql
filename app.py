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
    if os.path.exists("output/chart.png"):
        os.remove("output/chart.png")
    if os.path.exists("output/final_report.md"):
        os.remove("output/final_report.md")
    if os.path.exists("output/final_report.pdf"):
        os.remove("output/final_report.pdf")
    if os.path.exists("output/activity_log.json"):
        os.remove("output/activity_log.json")

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
    "and receive a comprehensive PDF report with charts and insights."
)

# --- User Inputs ---
st.sidebar.header("Configuration")
# Key inputs default from .env
openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", "")
)
gemini_api_key = st.sidebar.text_input(
    "Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", "")
)
db_connection_string = st.sidebar.text_input(
    "NeonDB Connection String",
    placeholder="postgresql://user:password@host:port/dbname",
    value=os.getenv("NEONDB_CONN_STR", "")
)

st.header("Ask Your Data a Question")
query = st.text_area(
    "Enter your question here:",
    placeholder="e.g., 'What were our total sales per month for the last year?'",
    height=150,
)

if st.button("Generate Report"):
    if not openai_api_key or not gemini_api_key or not db_connection_string or not query:
        st.error("Please provide all required inputs: OpenAI Key, Gemini Key, DB Connection String, and your query.")
    else:
        # Set the API key for the current process
        os.environ["OPENAI_API_KEY"] = openai_api_key
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        os.environ["NEONDB_CONN_STR"] = db_connection_string
        
        # Clean up old files before running
        cleanup_output_files()

        # Create placeholder for activity log
        activity_placeholder = st.empty()
        status_placeholder = st.empty()

        with status_placeholder:
            st.info("🤖 Your AI Data Scientist is starting up...")

        try:
            # Initialize and run the crew
            cogniquery_crew = CogniQueryCrew(db_connection_string=db_connection_string)
            
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

            # Display the generated markdown report
            st.subheader("📊 Generated Analysis Report")
            st.markdown(result[0].raw, unsafe_allow_html=True)
            
            # Display chart image if generated
            chart_path = "output/chart.png"
            
            # Debug: List all files in output directory
            try:
                output_files = os.listdir("output")
                st.write(f"📁 Files in output directory: {output_files}")
            except Exception as e:
                st.write(f"📁 Could not list output directory: {e}")
            
            if os.path.exists(chart_path):
                st.subheader("📈 Generated Chart")
                st.image(chart_path, caption="Analysis Chart", use_column_width=True)
            else:
                st.warning("⚠️ Chart was not generated. Check the activity log for Python code execution details.")
                st.write(f"Looking for chart at: {os.path.abspath(chart_path)}")

        except Exception as e:
            with status_placeholder:
                st.error(f"❌ An error occurred: {e}")
        finally:
            # Keep the activity log visible after completion
            pass

st.sidebar.info(
    "**How it works:**\n"
    "1. **Business Analyst:** Refines your query.\n"
    "2. **Database Administrator:** Writes the SQL code.\n"
    "3. **Data Scientist:** Runs the query and creates charts.\n"
    "4. **Communications Strategist:** Compiles the final report.\n\n"
    "**🔍 Activity Log:** Watch the agents work in real-time! "
    "You'll see all SQL queries, tool usage, and progress updates as they happen."
)
