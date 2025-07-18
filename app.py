# app.py

import os
import streamlit as st
from dotenv import load_dotenv
from src.cogniquery_crew.crew import CogniQueryCrew

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

        with st.spinner("Your AI Data Scientist is on the case... 🕵️‍♂️"):
            try:
                # Initialize and run the crew
                cogniquery_crew = CogniQueryCrew(db_connection_string=db_connection_string)
                result = cogniquery_crew.crew().kickoff(inputs={'query': query})
                
                st.success("Report generated successfully!")

                # Display the generated markdown report
                st.subheader("Generated Markdown Report")
                st.markdown(result.raw, unsafe_allow_html=True)
                # Display chart image if generated
                chart_path = "output/chart.png"
                if os.path.exists(chart_path):
                    st.image(chart_path, caption="Chart")

            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                # Clean up generated files after the run
                cleanup_output_files()

st.sidebar.info(
    "**How it works:**\n"
    "1. **Prompt Enhancer:** Refines your query.\n"
    "2. **SQL Generator:** Writes the SQL code.\n"
    "3. **Data Analyst:** Runs the query and creates charts.\n"
    "4. **Report Generator:** Compiles the final PDF report."
)
