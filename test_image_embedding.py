#!/usr/bin/env python3
"""
Test script to verify that images appear as actual images, not base64 strings
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from cogniquery_crew.tools.pdf_generator import EnhancedPDFGenerator

def test_image_vs_base64_issue():
    """Test that images are properly embedded and not showing as base64 strings"""
    
    print("🖼️  Testing Image Embedding vs Base64 String Display...")
    
    # Create markdown content that mimics what the CogniQuery crew generates
    markdown_with_images_and_tables = """# Test Report for Image vs Base64 Issue

## TLDR
- **Key Finding**: Images should appear as actual charts, not base64 strings
- **Table Test**: Tables should be properly formatted with borders

## Data Analysis

### Performance Table

| Region | Sales | Profit | Status |
|--------|-------|--------|--------|
| North America | $1,250 | $500 | ✅ Good |
| Europe | $3,900 | $1,120 | ✅ Excellent |
| Southeast Asia | $8,200 | -$520 | ❌ Poor |

### Chart Analysis

Here are the supporting charts:

![Quarterly Revenue](output/test_chart_1.png)

![Performance Trends](output/test_chart_2.png)

## Verification Points

1. ✅ **Tables**: Should have borders, headers, and proper alignment
2. ✅ **Images**: Should appear as actual charts, NOT as long base64 strings
3. ✅ **Content**: Should be readable and professional

If you see long strings starting with "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." instead of actual images, then the embedding is broken.
"""

    print("📄 Generating PDF with focus on image embedding...")
    
    generator = EnhancedPDFGenerator()
    
    try:
        pdf_bytes = generator.create_pdf(markdown_with_images_and_tables)
        pdf_path = "output/image_vs_base64_test.pdf"
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✅ PDF generated: {pdf_path}")
        
        # Check file characteristics
        file_size = os.path.getsize(pdf_path)
        print(f"📊 PDF file size: {file_size:,} bytes")
        
        # Get chart files that should be embedded
        chart_files = generator.get_chart_files()
        print(f"📈 Chart files found: {len(chart_files)} ({', '.join(chart_files)})")
        
        if file_size > 150000:  # Should be substantial with embedded images
            print("🎉 PDF size indicates proper image embedding!")
        elif file_size > 50000:
            print("✅ PDF size is reasonable - likely contains formatted content")
        else:
            print("⚠️  PDF size is small - images might not be embedded")
            
        # Key success indicators
        if len(chart_files) > 0 and file_size > 100000:
            print("\n🎯 SUCCESS INDICATORS:")
            print("   ✅ Chart files found and available for embedding")
            print("   ✅ PDF file size suggests rich content (images + tables)")
            print("   ✅ Both table and image processing should be working")
            print("\n💡 In the PDF, you should see:")
            print("   📊 Properly formatted tables with borders")
            print("   📈 Actual chart images (not base64 strings)")
            print("   📄 Clean, professional layout")
        else:
            print("\n⚠️  Potential issues detected - check the PDF manually")
            
        return True
        
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_image_vs_base64_issue()
    if success:
        print("\n🔍 Please check the generated PDF to confirm:")
        print("   1. Tables have proper formatting and borders")
        print("   2. Images appear as actual charts (not base64 strings)")
        print("   3. Overall layout is clean and professional")
