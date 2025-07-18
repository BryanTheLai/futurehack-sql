#!/usr/bin/env python3
"""Test the complete CogniQuery crew to verify chart creation."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('.')

from src.cogniquery_crew.crew import CogniQueryCrew
from src.cogniquery_crew.tools.activity_logger import get_activity_logger

def test_simple_analysis():
    """Test the crew with a simple analysis that should create charts."""
    print("Testing CogniQuery crew chart creation...")
    
    # Clean output directory
    output_files = ["chart_1.png", "chart_2.png", "chart.png", "final_report.md"]
    for file in output_files:
        file_path = f"output/{file}"
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Removed existing {file_path}")
    
    # Get database connection
    db_conn = os.getenv("NEONDB_CONN_STR")
    if not db_conn:
        print("ERROR: NEONDB_CONN_STR not found in environment")
        return False
    
    # Create crew
    crew_instance = CogniQueryCrew(db_connection_string=db_conn)
    
    # Simple test query
    test_query = "Show me the relationship between discounts and profit with a chart"
    
    print(f"Testing query: {test_query}")
    
    try:
        # Run the crew
        result = crew_instance.crew().kickoff(inputs={'query': test_query})
        print(f"Crew execution completed")
        print(f"Result: {str(result)[:500]}...")
        
        # Check activity log
        logger = get_activity_logger()
        activities = logger.get_activities()
        
        sql_queries = [a for a in activities if a.get('type') == 'sql_query']
        python_code = [a for a in activities if a.get('type') == 'python_code']
        
        print(f"SQL queries executed: {len(sql_queries)}")
        print(f"Python code executed: {len(python_code)}")
        
        # Check for chart files
        chart_files = []
        if os.path.exists("output"):
            for file in os.listdir("output"):
                if file.endswith('.png'):
                    chart_files.append(file)
        
        print(f"Chart files created: {chart_files}")
        
        if chart_files:
            print("SUCCESS: Charts were created!")
            return True
        else:
            print("FAILED: No chart files found")
            print("Activity log:")
            for activity in activities[-10:]:  # Last 10 activities
                print(f"  {activity['type']}: {activity['content'][:100]}...")
            return False
        
    except Exception as e:
        print(f"Error running crew: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_analysis()
    sys.exit(0 if success else 1)
