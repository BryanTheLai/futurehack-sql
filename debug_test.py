#!/usr/bin/env python3
"""Quick test to trigger chart creation and see debug output."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('.')

from src.cogniquery_crew.crew import CogniQueryCrew

def test_simple_query():
    """Test with a very simple query to see if LocalCodeExecutor is called."""
    print("Testing simple query to see LocalCodeExecutor debug output...")
    
    # Clean output directory
    output_files = ["chart_1.png", "chart_2.png", "chart.png", "final_report.md"]
    for file in output_files:
        file_path = f"output/{file}"
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Get database connection
    db_conn = os.getenv("NEONDB_CONN_STR")
    if not db_conn:
        print("ERROR: NEONDB_CONN_STR not found in environment")
        return False
    
    # Create crew
    crew_instance = CogniQueryCrew(db_connection_string=db_conn)
    
    # Very simple test query
    test_query = "Create a simple chart showing discount vs profit"
    
    print(f"Testing query: {test_query}")
    print("Looking for 🐛 DEBUG messages...")
    
    try:
        # Run the crew - this should trigger the data analyst which should call LocalCodeExecutor
        result = crew_instance.crew().kickoff(inputs={'query': test_query})
        print("Crew execution completed")
        
        # Check for chart files
        chart_files = []
        if os.path.exists("output"):
            for file in os.listdir("output"):
                if file.endswith('.png'):
                    chart_files.append(file)
        
        print(f"Chart files created: {chart_files}")
        
        return len(chart_files) > 0
        
    except Exception as e:
        print(f"Error running crew: {e}")
        return False

if __name__ == "__main__":
    test_simple_query()
