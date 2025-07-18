# test_agent_behavior.py
# Test if the agent now uses Code Interpreter tool

import os
from src.cogniquery_crew.crew import CogniQueryCrew
from src.cogniquery_crew.tools.activity_logger import get_activity_logger

def test_agent_uses_code_interpreter():
    """Test that the agent actually uses Code Interpreter after SQL queries."""
    
    # Clear any existing output
    if os.path.exists("output"):
        for f in os.listdir("output"):
            if f.endswith('.png'):
                os.remove(os.path.join("output", f))
    
    # Set up database connection (use environment variable or default)
    db_connection = os.getenv("DATABASE_URL", "your_default_connection_string")
    
    # Create the crew
    crew_instance = CogniQueryCrew(db_connection_string=db_connection)
    
    # Test with a simple query
    test_query = "What are the top 3 sub-categories with the lowest profit in Southeast Asia?"
    
    print(f"Testing agent behavior with query: {test_query}")
    print("=" * 60)
    
    try:
        # Run the crew
        result = crew_instance.crew().kickoff(inputs={"query": test_query})
        
        print("Crew execution completed!")
        print("Result:")
        print(result)
        print("=" * 60)
        
        # Check the activity log for Code Interpreter usage
        logger = get_activity_logger()
        activities = logger.get_activities()
        
        print("Activity Log Analysis:")
        sql_queries = 0
        code_interpreter_usage = 0
        
        for activity in activities:
            if activity.get('type') == 'sql_query':
                sql_queries += 1
            elif activity.get('type') == 'python_code':
                code_interpreter_usage += 1
                
        print(f"SQL Queries executed: {sql_queries}")
        print(f"Code Interpreter calls: {code_interpreter_usage}")
        
        # Check if charts were created
        chart_files = []
        if os.path.exists("output"):
            chart_files = [f for f in os.listdir("output") if f.endswith('.png')]
        
        print(f"Chart files created: {chart_files}")
        
        # Determine if the test passed
        if code_interpreter_usage > 0 and len(chart_files) > 0:
            print("✅ SUCCESS: Agent is using Code Interpreter and creating charts!")
            return True
        elif code_interpreter_usage > 0:
            print("⚠️  PARTIAL: Agent used Code Interpreter but no charts found")
            return False
        else:
            print("❌ FAILED: Agent is NOT using Code Interpreter tool")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Crew execution failed: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_uses_code_interpreter()
    if success:
        print("\n🎉 The agent behavior has been fixed!")
    else:
        print("\n😞 The agent still needs more work to use Code Interpreter consistently.")
