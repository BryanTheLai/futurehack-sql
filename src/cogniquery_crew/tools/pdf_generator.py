# src/cogniquery_crew/tools/pdf_generator.py

import os
import glob
import re
import base64
import datetime
from typing import List

# Try to import PDF generation libraries
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class EnhancedPDFGenerator:
    """
    Enhanced PDF generator that can create PDFs with embedded charts and styled tables.
    Supports both WeasyPrint and ReportLab backends with graceful degradation.
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
    
    def get_chart_files(self) -> List[str]:
        """
        Find all chart files in the output directory.
        Returns a list of chart filenames.
        """
        chart_files = []
        
        if os.path.exists(self.output_dir):
            # Look for PNG files (charts)
            png_files = glob.glob(os.path.join(self.output_dir, "*.png"))
            chart_files = [os.path.basename(f) for f in png_files]
            # Sort for consistent ordering
            chart_files.sort()
        
        return chart_files
    
    def create_pdf(self, markdown_content: str, chart_files: List[str] = None) -> bytes:
        """
        Create a PDF report with embedded images and proper table formatting.
        """
        if chart_files is None:
            chart_files = self.get_chart_files()
            
        if WEASYPRINT_AVAILABLE:
            return self._create_pdf_with_weasyprint(markdown_content, chart_files)
        elif REPORTLAB_AVAILABLE:
            return self._create_pdf_with_reportlab(markdown_content, chart_files)
        else:
            raise Exception("PDF generation is unavailable. Neither WeasyPrint nor ReportLab are properly installed.")
    
    def _create_pdf_with_weasyprint(self, markdown_content: str, chart_files: List[str]) -> bytes:
        """
        Enhanced PDF generation using WeasyPrint with image embedding.
        """
        try:
            from markdown_it import MarkdownIt
            
            # Make a copy of the markdown content to avoid modifying the original
            pdf_content = markdown_content

            # --- 1. Find chart references and replace with Base64 embedded images ---
            for chart_file in chart_files:
                chart_path = os.path.join(self.output_dir, chart_file)
                if os.path.exists(chart_path):
                    try:
                        # Read image data in binary format
                        with open(chart_path, "rb") as f:
                            image_data = f.read()
                        # Encode to Base64
                        base64_image = base64.b64encode(image_data).decode("utf-8")
                        # Create the HTML img tag with embedded data
                        img_tag = f'<img src="data:image/png;base64,{base64_image}" alt="{chart_file}" style="max-width: 100%; height: auto; margin: 20px auto; display: block;">'
                        
                        # Replace various possible markdown image references
                        chart_name = chart_file.split('.')[0]
                        pdf_content = pdf_content.replace(f"![{chart_name}]({chart_file})", img_tag)
                        pdf_content = pdf_content.replace(f"![Chart]({chart_file})", img_tag)
                        pdf_content = pdf_content.replace(f"![chart]({chart_file})", img_tag)
                        pdf_content = pdf_content.replace(chart_file, img_tag)

                    except Exception as e:
                        print(f"⚠️ Could not embed chart {chart_file}: {e}")

            # --- 2. Convert the final Markdown to HTML ---
            md = MarkdownIt()
            html_content = md.render(pdf_content)
            
            # Add a header with timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Wrap in a complete HTML document
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>CogniQuery Analysis Report</title>
            </head>
            <body>
                <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #003366; padding-bottom: 10px;">
                    <h1 style="color: #003366; margin-bottom: 5px;">CogniQuery Analysis Report</h1>
                    <p style="color: #666; font-size: 12pt; margin: 0;">Generated on {timestamp}</p>
                </div>
                {html_content}
            </body>
            </html>
            """

            # --- 3. Define CSS for styling the PDF ---
            css = CSS(string='''
                @page { size: A4; margin: 2cm; }
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; font-size: 11pt; color: #333; }
                h1, h2, h3 { color: #003366; border-bottom: 2px solid #f0f2f6; padding-bottom: 5px; margin-top: 25px; }
                h1 { font-size: 22pt; margin-top: 0; }
                h2 { font-size: 16pt; }
                h3 { font-size: 13pt; }
                h4, h5, h6 { color: #555; margin-top: 20px; }
                table { border-collapse: collapse; width: 100%; margin-bottom: 1.5em; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 10pt; }
                th { background-color: #f2f2f6; font-weight: bold; }
                img { display: block; margin: 20px auto; max-width: 90%; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                code { background-color: #f0f2f6; padding: 2px 4px; border-radius: 3px; font-family: 'Monaco', 'Consolas', monospace; font-size: 9pt; }
                pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border-left: 4px solid #007acc; }
                blockquote { border-left: 4px solid #ddd; padding-left: 15px; margin-left: 0; font-style: italic; color: #666; }
                ul, ol { margin-bottom: 15px; }
                li { margin-bottom: 5px; }
                p { margin-bottom: 12px; }
            ''')
            
            # --- 4. Generate the PDF in memory ---
            pdf_bytes = HTML(string=full_html).write_pdf(stylesheets=[css])
            return pdf_bytes
        except Exception as e:
            raise Exception(f"Failed to generate PDF with WeasyPrint: {e}")
    
    def _create_pdf_with_reportlab(self, markdown_content: str, chart_files: List[str]) -> bytes:
        """
        Enhanced PDF generation using ReportLab with proper table and image handling.
        """
        try:
            # Create a BytesIO buffer to hold the PDF
            buffer = BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                  rightMargin=72, leftMargin=72,
                                  topMargin=72, bottomMargin=18)
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Define comprehensive custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#003366'),
                alignment=1,  # Center alignment
                spaceAfter=30,
                fontName='Helvetica-Bold'
            )
            
            h1_style = ParagraphStyle(
                'CustomH1',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#003366'),
                spaceBefore=25,
                spaceAfter=15,
                fontName='Helvetica-Bold'
            )
            
            h2_style = ParagraphStyle(
                'CustomH2',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#003366'),
                spaceBefore=20,
                spaceAfter=12,
                fontName='Helvetica-Bold'
            )
            
            h3_style = ParagraphStyle(
                'CustomH3',
                parent=styles['Heading3'],
                fontSize=14,
                textColor=colors.HexColor('#555555'),
                spaceBefore=15,
                spaceAfter=10,
                fontName='Helvetica-Bold'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=16,
                fontName='Helvetica'
            )
            
            bullet_style = ParagraphStyle(
                'CustomBullet',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                leftIndent=20,
                bulletIndent=10,
                leading=14,
                fontName='Helvetica'
            )
            
            # Build the PDF content
            story = []
            
            # Add title and timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph("CogniQuery Analysis Report", title_style))
            story.append(Paragraph(f"Generated on {timestamp}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Process the markdown content line by line with proper formatting
            lines = markdown_content.split('\n')
            current_paragraph = []
            in_table = False
            table_rows = []
            
            for line in lines:
                line = line.strip()
                
                # Empty line handling
                if not line:
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph)
                        para_text = self._process_markdown_formatting(para_text)
                        story.append(Paragraph(para_text, body_style))
                        current_paragraph = []
                    continue
                
                # Handle tables
                if '|' in line and not line.startswith('#'):
                    if not re.match(r'^[\|\s\-:]+$', line):  # Skip separator lines
                        table_rows.append(line)
                        in_table = True
                    continue
                else:
                    # If we were in a table and now we're not, render the table
                    if in_table and table_rows:
                        table = self._create_table_from_markdown(table_rows)
                        if table:
                            story.append(table)
                            story.append(Spacer(1, 12))
                        table_rows = []
                        in_table = False
                
                # Handle headers
                if line.startswith('### '):
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph)
                        para_text = self._process_markdown_formatting(para_text)
                        story.append(Paragraph(para_text, body_style))
                        current_paragraph = []
                    header_text = self._process_markdown_formatting(line[4:])
                    story.append(Paragraph(header_text, h3_style))
                    
                elif line.startswith('## '):
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph)
                        para_text = self._process_markdown_formatting(para_text)
                        story.append(Paragraph(para_text, body_style))
                        current_paragraph = []
                    header_text = self._process_markdown_formatting(line[3:])
                    story.append(Paragraph(header_text, h2_style))
                    
                elif line.startswith('# '):
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph)
                        para_text = self._process_markdown_formatting(para_text)
                        story.append(Paragraph(para_text, body_style))
                        current_paragraph = []
                    header_text = self._process_markdown_formatting(line[2:])
                    story.append(Paragraph(header_text, h1_style))
                    
                # Handle bullet points
                elif line.startswith('- ') or line.startswith('* '):
                    if current_paragraph:
                        para_text = ' '.join(current_paragraph)
                        para_text = self._process_markdown_formatting(para_text)
                        story.append(Paragraph(para_text, body_style))
                        current_paragraph = []
                    bullet_text = self._process_markdown_formatting(line[2:])
                    story.append(Paragraph(f"• {bullet_text}", bullet_style))
                    
                # Skip markdown image references (we'll add charts separately)
                elif re.match(r'!\[.*\]\(.*\)', line):
                    continue
                    
                # Regular paragraph text
                else:
                    current_paragraph.append(line)
            
            # Handle any remaining paragraph
            if current_paragraph:
                para_text = ' '.join(current_paragraph)
                para_text = self._process_markdown_formatting(para_text)
                story.append(Paragraph(para_text, body_style))
            
            # Add charts with proper formatting
            for chart_file in chart_files:
                chart_path = os.path.join(self.output_dir, chart_file)
                if os.path.exists(chart_path):
                    try:
                        story.append(Spacer(1, 30))
                        chart_title = chart_file.replace('.png', '').replace('_', ' ').title()
                        story.append(Paragraph(f"Chart: {chart_title}", h3_style))
                        story.append(Spacer(1, 10))
                        
                        # Add the image with appropriate sizing
                        img = Image(chart_path, width=6.5*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 20))
                    except Exception as e:
                        story.append(Paragraph(f"Error loading chart {chart_file}: {e}", body_style))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            return pdf_bytes
        except Exception as e:
            raise Exception(f"Failed to generate PDF with ReportLab: {e}")
    
    def _process_markdown_formatting(self, text: str) -> str:
        """
        Process basic markdown formatting like **bold**, *italic*, `code`, etc.
        """
        # Handle bold text **text**
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        
        # Handle italic text *text*
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        # Handle inline code `code`
        text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#d63384">\1</font>', text)
        
        # Handle links [text](url) - just show the text for PDF
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        return text
    
    def _create_table_from_markdown(self, table_rows: List[str]) -> Table:
        """
        Create a ReportLab Table from markdown table rows.
        """
        if not table_rows:
            return None
        
        # Parse table rows
        parsed_rows = []
        for row in table_rows:
            # Split by | and clean up cells
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            # Process markdown formatting in each cell
            formatted_cells = [self._process_markdown_formatting(cell) for cell in cells]
            if formatted_cells:  # Only add non-empty rows
                parsed_rows.append(formatted_cells)
        
        if not parsed_rows:
            return None
        
        # Determine column widths based on content
        max_cols = max(len(row) for row in parsed_rows) if parsed_rows else 1
        col_width = 6.5 * inch / max_cols
        col_widths = [col_width] * max_cols
        
        # Create the table
        table = Table(parsed_rows, colWidths=col_widths)
        
        # Style the table
        table_style = [
            # Header styling (first row)
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]
        
        # Add alternating row colors for readability
        for i in range(1, len(parsed_rows)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
        
        table.setStyle(TableStyle(table_style))
        
        return table


class TLDRExtractor:
    """
    Utility class for extracting TL;DR summaries from markdown content.
    """
    
    @staticmethod
    def extract_tldr(markdown_content: str) -> str:
        """
        Extract the TL;DR section from the markdown report for Slack message.
        Returns a clean, formatted summary suitable for Slack.
        """
        lines = markdown_content.split('\n')
        tldr_content = []
        capturing = False
        
        for line in lines:
            # Look for TL;DR section start
            if re.search(r'#{1,3}\s*TL;?DR\b', line, re.IGNORECASE):
                capturing = True
                continue
            # Stop capturing at the next major section
            elif capturing and line.startswith('---'):
                break
            elif capturing and re.match(r'^#{1,3}\s+', line):
                break
            elif capturing and line.strip():
                # Clean up markdown formatting for Slack
                clean_line = line.strip()
                # Convert **bold** to *bold* for Slack
                clean_line = re.sub(r'\*\*(.*?)\*\*', r'*\1*', clean_line)
                # Remove markdown list indicators and add Slack-style bullets
                if clean_line.startswith('- '):
                    clean_line = f"• {clean_line[2:]}"
                tldr_content.append(clean_line)
        
        return '\n'.join(tldr_content).strip()
    
    @staticmethod
    def extract_key_metrics(markdown_content: str) -> dict:
        """
        Extract key metrics from the markdown content.
        Returns a dictionary of metrics for quick reference.
        """
        metrics = {}
        
        # Look for common metric patterns
        # This could be enhanced with more sophisticated parsing
        lines = markdown_content.split('\n')
        
        for line in lines:
            # Look for monetary values
            money_matches = re.findall(r'[\$][\d,]+\.?\d*', line)
            if money_matches:
                metrics.setdefault('monetary_values', []).extend(money_matches)
            
            # Look for percentages
            percent_matches = re.findall(r'\d+\.?\d*%', line)
            if percent_matches:
                metrics.setdefault('percentages', []).extend(percent_matches)
        
        return metrics
