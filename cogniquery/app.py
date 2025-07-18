# app.py

import os
import streamlit as st
from dotenv import load_dotenv
from src.cogniquery_crew.crew import CogniQueryCrew

# Load environment variables
load_dotenv()

def cleanup_output_files():
    """Removes generated files from the output directory to keep it clean."""
    if os.path.exists("cogniquery/output/chart.png"):
        os.remove("cogniquery/output/chart.png")
    if os.path.exists("cogniquery/output/final_report.md"):
        os.remove("cogniquery/output/final_report.md")

st.set_page_config(page_title="CogniQuery", page_icon="🤖")
st.title("CogniQuery 🤖")
st.subheader("Your AI Data Scientist")

st.write(
    "Welcome to CogniQuery! Connect to your NeonDB database, ask a question in plain English, "
    "and receive a comprehensive PDF report with charts and insights."
)

# --- User Inputs ---
st.sidebar.header("Configuration")
openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", "")
)
db_connection_string = st.sidebar.text_input(
    "NeonDB Connection String",
    placeholder="postgresql://user:password@host:port/dbname",
)

st.header("Ask Your Data a Question")
query = st.text_area(
    "Enter your question here:",
    placeholder="e.g., 'What were our total sales per month for the last year?'",
    height=150,
)

if st.button("Generate Report"):
    if not openai_api_key or not db_connection_string or not query:
        st.error("Please provide all required inputs: API Key, DB Connection String, and your query.")
    else:
        # Set the API key for the current process
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        # Clean up old files before running
        cleanup_output_files()

        with st.spinner("Your AI Data Scientist is on the case... 🕵️‍♂️"):
            try:
                # Initialize and run the crew
                cogniquery_crew = CogniQueryCrew(db_connection_string=db_connection_string)
                result = cogniquery_crew.crew().kickoff(inputs={'query': query})
                
                st.success("Report generated successfully!")

                # Display the markdown report for debugging/review
                st.subheader("Generated Markdown Report")
                with open("cogniquery/output/final_report.md", "r") as f:
                    st.markdown(f.read())

                # Provide download link for the PDF
                report_path = "cogniquery/output/final_report.pdf"
                
                # Use the reporting tool to create the final PDF from the markdown output
                cogniquery_crew.report_tool.create_report(
                    markdown_content=result.raw,
                    report_file_path=report_path
                )

                with open(report_path, "rb") as pdf_file:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_file,
                        file_name="CogniQuery_Report.pdf",
                        mime="application/pdf",
                    )
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
