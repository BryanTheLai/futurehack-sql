# Test Code Interpreter Tool Functionality

import os
import sys
sys.path.append('src')

from src.cogniquery_crew.tools.logged_code_interpreter import LoggedCodeInterpreterTool

def test_chart_creation():
    """Test that the Code Interpreter can create charts properly."""
    
    # Initialize the tool
    code_interpreter = LoggedCodeInterpreterTool()
    
    # Test code that creates a simple chart
    test_code = '''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Create sample data
categories = ['A', 'B', 'C', 'D']
values = [23, 45, 56, 78]

# Create a bar chart
plt.figure(figsize=(8, 6))
plt.bar(categories, values, color=['red', 'green', 'blue', 'orange'])
plt.title('Test Chart - Code Interpreter')
plt.xlabel('Categories')
plt.ylabel('Values')
plt.grid(True, alpha=0.3)

# Save the chart
plt.savefig('output/test_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Test chart created successfully!")
print(f"Current working directory: {os.getcwd()}")

# Check if file was created
import os
if os.path.exists('output/test_chart.png'):
    print("✅ Chart file exists at output/test_chart.png")
else:
    print("❌ Chart file was not created")

# List files in output directory
if os.path.exists('output'):
    files = os.listdir('output')
    print(f"Files in output directory: {files}")
else:
    print("❌ Output directory does not exist")
'''
    
    print("🧪 Testing Code Interpreter tool...")
    
    # Execute the test code
    result = code_interpreter._run(code=test_code)
    
    print("\n📋 Code Interpreter Result:")
    print(result)
    
    # Check if the chart was actually created
    if os.path.exists('output/test_chart.png'):
        print("\n✅ SUCCESS: Chart was created successfully!")
        print(f"Chart size: {os.path.getsize('output/test_chart.png')} bytes")
    else:
        print("\n❌ FAILURE: Chart was not created")
        if os.path.exists('output'):
            files = os.listdir('output')
            print(f"Files in output directory: {files}")
        else:
            print("Output directory does not exist")

if __name__ == "__main__":
    test_chart_creation()
