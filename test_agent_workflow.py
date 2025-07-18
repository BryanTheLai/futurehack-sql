# test_agent_workflow.py
# Test the exact workflow the agent should follow

import os
from src.cogniquery_crew.tools.sql_executor_tool import SQLExecutorTool
from src.cogniquery_crew.tools.local_code_executor import LocalCodeExecutorTool

def test_agent_workflow():
    """Test the exact workflow: SQL -> Code Interpreter -> Chart"""
    
    # Step 1: Execute SQL (similar to what agent does)
    sql_tool = SQLExecutorTool()
    
    # Use the same query from the activity log
    sql_query = """
    SELECT p.sub_category, SUM(o.sales) AS total_sales, SUM(o.profit) AS total_profit, AVG(o.discount) AS average_discount 
    FROM orders o 
    INNER JOIN products p ON o.product_id = p.product_id 
    INNER JOIN regions r ON o.region_id = r.region_id 
    WHERE r.region_name = 'Southeast Asia' 
    GROUP BY p.sub_category 
    ORDER BY total_profit ASC 
    LIMIT 3;
    """
    
    print("Step 1: Executing SQL query...")
    sql_result = sql_tool._run(sql_query=sql_query)
    print("SQL Result:")
    print(sql_result)
    print("\n" + "="*50 + "\n")
    
    # Step 2: Use Code Interpreter to create charts with the SQL result
    code_tool = LocalCodeExecutorTool()
    
    # Create code that processes the SQL result and creates charts
    chart_code = f'''
import pandas as pd
import matplotlib.pyplot as plt
import io

# Extract just the CSV portion from the SQL result
full_result = """{sql_result}"""

# Find the CSV portion more reliably
lines = full_result.split('\\n')
csv_lines = []
in_csv = False

for line in lines:
    if 'sub_category,total_sales,total_profit,average_discount' in line:
        in_csv = True
        csv_lines.append(line)
        continue
    elif in_csv and line.strip() and not line.startswith('NEXT STEP'):
        # Only add non-empty lines that contain data
        csv_lines.append(line)
    elif in_csv and (line.startswith('NEXT STEP') or 'NEXT STEP' in line):
        break

csv_data = '\\n'.join(csv_lines)
print("Extracted CSV data:")
print(repr(csv_data))

# Convert to DataFrame
df = pd.read_csv(io.StringIO(csv_data))

print("Data loaded:")
print(df)
print(f"Number of rows: {{len(df)}}")

# Only create chart if we have data
if len(df) > 0:
    # Create chart
    plt.figure(figsize=(12, 6))
    plt.bar(df['sub_category'], df['total_profit'], 
            color=['red' if x < 0 else 'green' for x in df['total_profit']])
    plt.title('Profit by Sub-Category (Southeast Asia) - Lowest Performing')
    plt.ylabel('Total Profit ($)')
    plt.xlabel('Sub-Category')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()

    # Save the chart
    plt.savefig('output/workflow_test_chart.png', dpi=300, bbox_inches='tight')
    plt.close()

    print("Chart created and saved!")
    print("Chart saved as: output/workflow_test_chart.png")
else:
    print("No data found to create chart!")
'''
    
    print("Step 2: Creating chart with Code Interpreter...")
    chart_result = code_tool._run(code=chart_code)
    print("Chart Creation Result:")
    print(chart_result)
    print("\n" + "="*50 + "\n")
    
    # Step 3: Verify chart was created
    chart_path = "output/workflow_test_chart.png"
    if os.path.exists(chart_path):
        file_size = os.path.getsize(chart_path)
        print(f"✅ SUCCESS: Workflow completed successfully!")
        print(f"   Chart created: {chart_path}")
        print(f"   File size: {file_size} bytes")
    else:
        print(f"❌ FAILED: Chart was not created")
    
    # List all charts in output
    if os.path.exists("output"):
        png_files = [f for f in os.listdir("output") if f.endswith('.png')]
        print(f"All PNG files in output: {png_files}")

if __name__ == "__main__":
    test_agent_workflow()
