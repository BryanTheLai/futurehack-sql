# Test plt.savefig() functionality with the exact pattern the agent should use

from src.cogniquery_crew.tools.logged_code_interpreter import LoggedCodeInterpreterTool

def test_chart_generation():
    """Test that the Code Interpreter tool can create charts using plt.savefig()"""
    
    print("🧪 Testing plt.savefig() chart generation...")
    
    code_interpreter = LoggedCodeInterpreterTool()
    
    # Test code that mimics what the agent should do
    test_code = '''
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Create sample data (simulating SQL results)
categories = ['Tables', 'Bookcases', 'Kitchen', 'Chairs', 'Phones', 'Laptops']
profits = [-930, -210, -80, 150, 250, 350]
discounts = [0.50, 0.60, 0.40, 0.10, 0.00, 0.15]

# Create Chart 1: Profit by Category
plt.figure(figsize=(10, 6))
colors = ['red' if p < 0 else 'green' for p in profits]
plt.bar(categories, profits, color=colors)
plt.title('Profit by Sub-Category (Southeast Asia)', fontsize=14, fontweight='bold')
plt.xlabel('Sub-Category')
plt.ylabel('Total Profit ($)')
plt.xticks(rotation=45)
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('output/chart_1.png', dpi=300, bbox_inches='tight')
plt.close()

# Create Chart 2: Discount vs Profit Scatter
plt.figure(figsize=(10, 6))
plt.scatter(discounts, profits, s=100, alpha=0.7, c=colors)
for i, cat in enumerate(categories):
    plt.annotate(cat, (discounts[i], profits[i]), xytext=(5, 5), 
                textcoords='offset points', fontsize=9)
plt.title('Discount Rate vs Profit Analysis', fontsize=14, fontweight='bold')
plt.xlabel('Discount Rate')
plt.ylabel('Total Profit ($)')
plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
plt.axvline(x=0.25, color='orange', linestyle='--', alpha=0.5, label='25% Discount Threshold')
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('output/chart_2.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ Charts created successfully using plt.savefig()")
print("Chart 1: output/chart_1.png")
print("Chart 2: output/chart_2.png")
'''
    
    # Execute the test code
    result = code_interpreter._run(code=test_code)
    
    print("\n📋 Code Interpreter Result:")
    print(result)
    
    # Check if charts were created
    import os
    output_dir = "output"
    if os.path.exists(output_dir):
        png_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        if png_files:
            print(f"\n✅ SUCCESS: Found {len(png_files)} chart file(s):")
            for png_file in png_files:
                file_path = os.path.join(output_dir, png_file)
                file_size = os.path.getsize(file_path)
                print(f"  - {png_file} ({file_size:,} bytes)")
        else:
            print("\n❌ FAILED: No PNG files found in output directory")
    else:
        print("\n❌ FAILED: Output directory does not exist")

if __name__ == "__main__":
    test_chart_generation()
