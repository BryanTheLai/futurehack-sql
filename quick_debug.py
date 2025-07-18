#!/usr/bin/env python3
"""Quick test with minimal crew setup to see debug output."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('.')

from src.cogniquery_crew.crew import CogniQueryCrew

def test_minimal():
    """Test with minimal crew to see debug output."""
    print("Testing minimal crew to see LocalCodeExecutor debug output...")
    
    # Clean output directory first
    for file in ["chart_1.png", "chart_2.png", "chart.png", "final_report.md"]:
        file_path = f"output/{file}"
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db_conn = os.getenv("NEONDB_CONN_STR")
    if not db_conn:
        print("ERROR: NEONDB_CONN_STR not found")
        return
    
    crew_instance = CogniQueryCrew(db_connection_string=db_conn)
    
    # Very simple query that should trigger chart creation
    query = "Create a chart with profit vs discount"
    
    print(f"Query: {query}")
    print("🐛 Looking for DEBUG messages...")
    
    try:
        result = crew_instance.crew().kickoff(inputs={'query': query})
        print("✅ Crew completed")
        
        # Check for any chart files
        chart_files = []
        if os.path.exists("output"):
            for file in os.listdir("output"):
                if file.endswith('.png'):
                    chart_files.append(file)
        
        print(f"📊 Chart files: {chart_files}")
        return len(chart_files) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_minimal()
