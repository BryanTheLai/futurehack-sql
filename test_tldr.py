#!/usr/bin/env python3

"""Test script for TLDR extraction functionality"""

from src.cogniquery_crew.tools.pdf_generator import TLDRExtractor

def test_tldr_extraction():
    """Test the TLDR extraction functionality"""
    
    print("🧪 Testing TLDR Extraction...")
    
    # Read test report
    try:
        with open('test_report.md', 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ Read test report ({len(content)} characters)")
    except Exception as e:
        print(f"❌ Error reading test report: {e}")
        return
    
    # Extract TLDR
    try:
        extractor = TLDRExtractor()
        tldr = extractor.extract_tldr(content)
        print(f"✅ TLDR extracted ({len(tldr)} characters)")
        
        print("\n" + "="*60)
        print("EXTRACTED TLDR:")
        print("="*60)
        print(tldr)
        print("="*60)
        
        # Test if it looks reasonable
        if len(tldr) > 50 and "Quantitative" in tldr and "Qualitative" in tldr:
            print("✅ TLDR content looks good!")
        else:
            print("⚠️  TLDR content may not be extracted correctly")
            
    except Exception as e:
        print(f"❌ Error extracting TLDR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tldr_extraction()
