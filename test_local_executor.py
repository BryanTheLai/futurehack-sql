# test_local_executor.py
# Test the LocalCodeExecutorTool specifically

import os
from src.cogniquery_crew.tools.local_code_executor import LocalCodeExecutorTool

def test_local_chart_creation():
    """Test that the LocalCodeExecutorTool can create charts."""
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Create the tool
    code_tool = LocalCodeExecutorTool()
    
    # Test code that creates a simple chart
    test_code = '''
import matplotlib.pyplot as plt
import pandas as pd
import io

# Sample CSV data (similar to what SQLExecutor returns)
csv_data = """sub_category,total_sales,total_profit
Tables,3000.0,-930.0
Bookcases,800.0,-210.0
Kitchen,450.0,-80.0"""

# Convert to DataFrame
df = pd.read_csv(io.StringIO(csv_data))

# Create chart
plt.figure(figsize=(10, 6))
plt.bar(df['sub_category'], df['total_profit'], color=['red' if x < 0 else 'green' for x in df['total_profit']])
plt.title('Profit by Sub-Category (Southeast Asia)')
plt.ylabel('Total Profit ($)')
plt.xlabel('Sub-Category')
plt.xticks(rotation=45)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Save the chart
plt.savefig('output/test_local_chart.png', dpi=300, bbox_inches='tight')
plt.close()

print("Local test chart created successfully!")
print("Chart saved as: output/test_local_chart.png")
'''
    
    # Run the code
    result = code_tool._run(code=test_code)
    print("Tool execution result:")
    print(result)
    
    # Check if the chart was created
    chart_path = "output/test_local_chart.png"
    if os.path.exists(chart_path):
        print(f"✅ SUCCESS: Chart was created at {chart_path}")
        file_size = os.path.getsize(chart_path)
        print(f"   File size: {file_size} bytes")
    else:
        print(f"❌ FAILED: Chart was not created at {chart_path}")
    
    # List all files in output directory
    if os.path.exists("output"):
        files = os.listdir("output")
        print(f"Files in output directory: {files}")
    else:
        print("Output directory does not exist")

if __name__ == "__main__":
    test_local_chart_creation()
