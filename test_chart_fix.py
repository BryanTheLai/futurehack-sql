#!/usr/bin/env python3
"""Test script to verify LocalCodeExecutor tool can create charts."""

import os
import sys
sys.path.append('.')

from src.cogniquery_crew.tools.local_code_executor import LocalCodeExecutorTool

def test_chart_creation():
    """Test if LocalCodeExecutor can create a simple chart."""
    print("Testing LocalCodeExecutor chart creation...")
    
    # Remove any existing chart files
    chart_path = "output/test_chart.png"
    if os.path.exists(chart_path):
        os.remove(chart_path)
        print(f"Removed existing {chart_path}")
    
    # Create tool instance
    tool = LocalCodeExecutorTool()
    print(f"Tool name: {tool.name}")
    
    # Test code that creates a simple chart
    test_code = '''
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import os

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Create a simple test chart
plt.figure(figsize=(8, 6))
plt.plot([1, 2, 3, 4], [10, 20, 15, 25], marker='o')
plt.title('Test Chart - LocalCodeExecutor')
plt.xlabel('X Values')
plt.ylabel('Y Values')
plt.grid(True)
plt.savefig('output/test_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("Test chart created successfully!")
'''
    
    # Execute the code
    result = tool._run(code=test_code)
    print(f"Execution result: {result}")
    
    # Check if chart was created
    if os.path.exists(chart_path):
        print(f"SUCCESS: Chart created at {chart_path}")
        file_size = os.path.getsize(chart_path)
        print(f"File size: {file_size} bytes")
    else:
        print(f"FAILED: Chart not found at {chart_path}")
    
    return os.path.exists(chart_path)

if __name__ == "__main__":
    success = test_chart_creation()
    sys.exit(0 if success else 1)
