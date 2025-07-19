#!/usr/bin/env python3
"""
Test script specifically for table rendering in PDFs
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cogniquery_crew.tools.pdf_generator import EnhancedPDFGenerator

def test_table_rendering():
    """Test table rendering specifically"""
    
    print("🧪 Testing Table Rendering in PDF...")
    
    # Create markdown with various table formats
    markdown_with_tables = """# Table Rendering Test

## Simple Table

| Region | Sales | Profit |
|--------|-------|--------|
| North America | $1,250.00 | $500.00 |
| Europe | $3,900.00 | $1,120.00 |
| Southeast Asia | $8,200.00 | -$520.00 |

## Complex Table

| Month | SE Asia Sales | Sales % Change | SE Asia Profit | Profit % Change |
|-------|---------------|----------------|----------------|-----------------|
| 2024-10-01 | 1200.00 | - | 120.00 | - |
| 2024-11-01 | 1050.00 | -12.50% | 70.00 | -41.67% |
| 2025-03-01 | 1500.00 | 42.86% | 250.00 | 257.14% |

## Analysis Summary

The tables above show regional performance data with proper formatting including:

- **Bold headers** with background colors
- Proper cell borders and padding  
- Monetary values with proper alignment
- Percentage changes clearly indicated

This ensures all table data is clearly readable in the PDF output.
"""

    print("📄 Generating PDF with table content...")
    
    generator = EnhancedPDFGenerator()
    
    try:
        pdf_bytes = generator.create_pdf(markdown_with_tables)
        pdf_path = "output/table_test_report.pdf"
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✅ Table test PDF generated: {pdf_path}")
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        print(f"📊 PDF file size: {file_size:,} bytes")
        
        if file_size > 30000:  # Should be a reasonable size for formatted tables
            print("🎉 PDF appears to contain properly formatted tables!")
        else:
            print("⚠️  PDF might not have properly formatted tables")
            
        return True
        
    except Exception as e:
        print(f"❌ Table PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_table_rendering()
    if success:
        print("\n✅ Table rendering test completed! Check the PDF to verify tables are properly formatted.")
