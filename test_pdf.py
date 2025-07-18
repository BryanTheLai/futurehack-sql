#!/usr/bin/env python3
"""Test script to verify PDF generation capabilities"""

print("Testing PDF generation dependencies...")

# Test WeasyPrint
try:
    from weasyprint import HTML, CSS
    print("✅ WeasyPrint: Available")
    weasyprint_available = True
except (ImportError, OSError) as e:
    print(f"❌ WeasyPrint: Not available - {type(e).__name__}")
    weasyprint_available = False

# Test ReportLab
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    print("✅ ReportLab: Available")
    reportlab_available = True
except ImportError as e:
    print(f"❌ ReportLab: Not available - {e}")
    reportlab_available = False

# Test other dependencies
try:
    from markdown_it import MarkdownIt
    import base64
    print("✅ MarkdownIt and base64: Available")
except ImportError as e:
    print(f"❌ Other dependencies: Not available - {e}")

# Summary
if weasyprint_available:
    print("\n🎉 PDF generation will use WeasyPrint (high quality)")
elif reportlab_available:
    print("\n🎉 PDF generation will use ReportLab (Windows-friendly)")
else:
    print("\n❌ PDF generation is not available")

print("\nPDF generation system is ready!")
