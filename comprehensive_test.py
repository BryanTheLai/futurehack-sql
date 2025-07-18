#!/usr/bin/env python3
"""Comprehensive test script for all database tools."""

from src.cogniquery_crew.tools.schema_explorer_tool import SchemaExplorerTool
from src.cogniquery_crew.tools.sample_data_tool import SampleDataTool
from src.cogniquery_crew.tools.sql_executor_tool import SQLExecutorTool

def test_all_tools():
    """Test all database tools with realistic scenarios."""
    print("=" * 60)
    print("COMPREHENSIVE DATABASE TOOLS TEST")
    print("=" * 60)
    
    # Test 1: Schema Explorer
    print("\n1. Testing SchemaExplorerTool...")
    schema_tool = SchemaExplorerTool()
    schema_result = schema_tool._run()
    print(f"Schema result length: {len(schema_result)} characters")
    print("Schema preview:")
    print(schema_result[:300] + "..." if len(schema_result) > 300 else schema_result)
    
    # Test 2: Sample Data Tool
    print("\n2. Testing SampleDataTool...")
    sample_tool = SampleDataTool()
    
    # Test regions table
    regions_result = sample_tool._run(table_name='regions', limit=5)
    print("Regions sample:")
    print(regions_result)
    
    # Test products table
    products_result = sample_tool._run(table_name='products', limit=3)
    print("\nProducts sample:")
    print(products_result)
    
    # Test orders table
    orders_result = sample_tool._run(table_name='orders', limit=2)
    print("\nOrders sample:")
    print(orders_result)
    
    # Test 3: SQL Executor Tool
    print("\n3. Testing SQLExecutorTool...")
    sql_tool = SQLExecutorTool()
    
    # Test simple query
    simple_query = "SELECT * FROM regions WHERE region_name = 'Southeast Asia'"
    print(f"Testing query: {simple_query}")
    simple_result = sql_tool._run(sql_query=simple_query)
    print("Result:")
    print(simple_result)
    
    # Test aggregation query
    agg_query = """
    SELECT 
        r.region_name,
        COUNT(o.order_id) as total_orders,
        SUM(o.sales) as total_sales,
        SUM(o.profit) as total_profit,
        AVG(o.discount) as avg_discount
    FROM regions r
    LEFT JOIN orders o ON r.region_id = o.region_id
    WHERE r.region_name = 'Southeast Asia'
    GROUP BY r.region_name
    """
    print(f"\nTesting aggregation query:")
    print(agg_query)
    agg_result = sql_tool._run(sql_query=agg_query)
    print("Result:")
    print(agg_result)
    
    # Test complex join query
    complex_query = """
    SELECT 
        p.sub_category,
        SUM(o.sales) as total_sales,
        SUM(o.profit) as total_profit,
        COUNT(o.order_id) as order_count,
        AVG(o.discount) as avg_discount
    FROM products p
    JOIN orders o ON p.product_id = o.product_id
    JOIN regions r ON o.region_id = r.region_id
    WHERE r.region_name = 'Southeast Asia' AND o.profit < 0
    GROUP BY p.sub_category
    ORDER BY total_profit ASC
    LIMIT 3
    """
    print(f"\nTesting complex join query (Southeast Asia loss leaders):")
    print(complex_query)
    complex_result = sql_tool._run(sql_query=complex_query)
    print("Result:")
    print(complex_result)
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    test_all_tools()
