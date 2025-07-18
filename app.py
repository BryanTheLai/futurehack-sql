# app.py

import os
import time
import json
import base64
import re
import streamlit as st
from dotenv import load_dotenv
from markdown_it import MarkdownIt
from src.cogniquery_crew.crew import CogniQueryCrew
from src.cogniquery_crew.tools.activity_logger import get_activity_logger

# Try to import WeasyPrint - it might not be available in all environments
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError):
    WEASYPRINT_AVAILABLE = False

# Try to import ReportLab as a fallback for Windows
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    from io import BytesIO
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Load environment variables
load_dotenv()
# Ensure output directory exists
os.makedirs("output", exist_ok=True)

def create_pdf_report(markdown_content, chart_files):
    """
    Generates a PDF report from markdown and chart images, embedding the images.
    Uses WeasyPrint if available, otherwise falls back to ReportLab.
    """
    if WEASYPRINT_AVAILABLE:
        return create_pdf_with_weasyprint(markdown_content, chart_files)
    elif REPORTLAB_AVAILABLE:
        return create_pdf_with_reportlab(markdown_content, chart_files)
    else:
        st.error("PDF generation is unavailable. Neither WeasyPrint nor ReportLab are properly installed.")
        return None

def create_pdf_with_weasyprint(markdown_content, chart_files):
    """
    Generates a PDF using WeasyPrint (preferred method).
    """
    try:
        # Make a copy of the markdown content to avoid modifying the original
        pdf_content = markdown_content

        # --- 1. Find chart references and replace with Base64 embedded images ---
        for chart_file in chart_files:
            chart_path = os.path.join("output", chart_file)
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
                    st.warning(f"Could not embed chart {chart_file}: {e}")

        # --- 2. Convert the final Markdown to HTML ---
        md = MarkdownIt()
        html_content = md.render(pdf_content)
        
        # Add a header with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
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
        st.error(f"Failed to generate PDF with WeasyPrint: {e}")
        return None

def create_pdf_with_reportlab(markdown_content, chart_files):
    """
    Generates a PDF using ReportLab (fallback method for Windows).
    """
    try:
        from datetime import datetime
        import re
        
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph("CogniQuery Analysis Report", title_style))
        story.append(Paragraph(f"Generated on {timestamp}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Process the markdown content line by line with proper formatting
        lines = markdown_content.split('\n')
        current_paragraph = []
        in_list = False
        in_table = False
        table_rows = []
        
        for line in lines:
            original_line = line
            line = line.strip()
            
            # Empty line handling
            if not line:
                # Finish any ongoing table
                if in_table and table_rows:
                    story.append(create_table_from_markdown(table_rows))
                    story.append(Spacer(1, 12))
                    table_rows = []
                    in_table = False
                
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    # Process basic markdown formatting in paragraphs
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                if in_list:
                    story.append(Spacer(1, 6))
                else:
                    story.append(Spacer(1, 12))
                in_list = False
                continue
            
            # Check if this line is a table row (contains |)
            if '|' in line and not line.startswith('#'):
                # Finish any current paragraph before starting table
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                
                # Skip table separator lines (like |---|---|)
                if not re.match(r'^[\|\s\-:]+$', line):
                    table_rows.append(line)
                    in_table = True
                    in_list = False
                continue
            else:
                # If we were in a table and now we're not, render the table
                if in_table and table_rows:
                    story.append(create_table_from_markdown(table_rows))
                    story.append(Spacer(1, 12))
                    table_rows = []
                    in_table = False
            
            # Handle headers
            if line.startswith('### '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                header_text = process_markdown_formatting(line[4:])
                story.append(Paragraph(header_text, h3_style))
                in_list = False
                
            elif line.startswith('## '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                header_text = process_markdown_formatting(line[3:])
                story.append(Paragraph(header_text, h2_style))
                in_list = False
                
            elif line.startswith('# '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                header_text = process_markdown_formatting(line[2:])
                story.append(Paragraph(header_text, h1_style))
                in_list = False
                
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('* '):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                bullet_text = process_markdown_formatting(line[2:])
                story.append(Paragraph(f"• {bullet_text}", bullet_style))
                in_list = True
                
            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                # Extract number and text
                match = re.match(r'^(\d+)\.\s(.+)', line)
                if match:
                    num, text = match.groups()
                    bullet_text = process_markdown_formatting(text)
                    story.append(Paragraph(f"{num}. {bullet_text}", bullet_style))
                in_list = True
                
            # Handle horizontal rules
            elif line.startswith('---') or line.startswith('***'):
                if current_paragraph:
                    para_text = ' '.join(current_paragraph)
                    para_text = process_markdown_formatting(para_text)
                    story.append(Paragraph(para_text, body_style))
                    current_paragraph = []
                story.append(Spacer(1, 10))
                # Add a line using a table
                line_table = Table([['_' * 50]], colWidths=[6*inch])
                line_table.setStyle(TableStyle([
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.lightgrey),
                    ('FONTSIZE', (0, 0), (-1, -1), 1),
                ]))
                story.append(line_table)
                story.append(Spacer(1, 10))
                in_list = False
                
            # Regular paragraph text
            else:
                current_paragraph.append(line)
                in_list = False
        
        # Handle any remaining table
        if in_table and table_rows:
            story.append(create_table_from_markdown(table_rows))
            story.append(Spacer(1, 12))
        
        # Add any remaining paragraph
        if current_paragraph:
            para_text = ' '.join(current_paragraph)
            para_text = process_markdown_formatting(para_text)
            story.append(Paragraph(para_text, body_style))
        
        # Add charts with proper formatting
        for chart_file in chart_files:
            chart_path = os.path.join("output", chart_file)
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
        st.error(f"Failed to generate PDF with ReportLab: {e}")
        return None

def process_markdown_formatting(text):
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

def create_table_from_markdown(table_rows):
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
        formatted_cells = [process_markdown_formatting(cell) for cell in cells]
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
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    
    # Apply alternating row colors for better readability
    for i in range(1, len(parsed_rows)):
        if i % 2 == 0:  # Even rows (0-indexed, so actually odd data rows)
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
    
    table.setStyle(TableStyle(table_style))
    
    return table

def cleanup_output_files():
    """Removes generated files from the output directory to keep it clean."""
    # Clean generated files from output directory
    file_patterns = ["chart.png", "final_report.md", "final_report.pdf", "activity_log.json"]
    
    for pattern in file_patterns:
        file_path = f"output/{pattern}"
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Cleaned up: {file_path}")
            except Exception as e:
                print(f"Could not remove {file_path}: {e}")
    
    # Also remove any other PNG files that might have been created
    if os.path.exists("output"):
        for file in os.listdir("output"):
            if file.endswith('.png'):
                try:
                    os.remove(f"output/{file}")
                    print(f"Cleaned up chart file: {file}")
                except Exception as e:
                    print(f"Could not remove chart file {file}: {e}")

def display_activity_log():
    """Display the current activity log in the UI."""
    try:
        logger = get_activity_logger()
        activities = logger.get_activities()
        status = logger.get_current_status()
        
        if not activities and not status.get('current_agent'):
            return
        
        st.subheader("🔍 Agent Activity Log")
        st.write("*Watch your AI agents work in real-time! All SQL queries and Python code execution are logged below.*")
        
        # Current status indicator
        if status.get('current_agent') and status.get('current_task'):
            st.info(f"🤖 **Currently Active:** {status['current_agent']} is working on {status['current_task'].replace('_', ' ')}")
        
        # Activity summary
        sql_count = len([a for a in activities if a.get('type') == 'sql_query'])
        python_count = len([a for a in activities if a.get('type') == 'python_code'])
        task_count = len([a for a in activities if a.get('type') == 'task_start'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("SQL Queries", sql_count)
        with col2:
            st.metric("Python Scripts", python_count)
        with col3:
            st.metric("Tasks Started", task_count)
        
        if not activities:
            return
            
        st.divider()
        
        for i, activity in enumerate(activities):
            timestamp = activity.get('timestamp', '').split('T')[1].split('.')[0] if activity.get('timestamp') else ''
            agent = activity.get('agent', 'Unknown')
            activity_type = activity.get('type', 'unknown')
            content = activity.get('content', '')
            details = activity.get('details', {})
            
            # Create different styling for different activity types
            if activity_type == 'sql_query':
                st.markdown(f"**🗄️ [{timestamp}] {agent} - SQL Query Execution**")
                st.code(content, language='sql')
                if details.get('result_preview'):
                    st.success("✅ Query executed successfully")
                    with st.expander("View Query Results"):
                        st.text(details['result_preview'])
                        
            elif activity_type == 'python_code':
                st.markdown(f"**🐍 [{timestamp}] {agent} - Python Code Execution**")
                st.code(content, language='python')
                if details.get('result'):
                    with st.expander("View Execution Results"):
                        st.text(details['result'])
                        
            elif activity_type == 'task_start':
                st.markdown(f"**🎯 [{timestamp}] {agent} - Task Started**")
                st.info(f"**{details.get('task_name', 'Unknown Task')}**")
                with st.expander("Task Description"):
                    st.write(details.get('description', content))
                    
            elif activity_type == 'tool_usage':
                st.markdown(f"**🛠️ [{timestamp}] {agent} - {details.get('tool_name', 'Tool')} Usage**")
                st.write(f"**Action:** {details.get('action', content)}")
                if details.get('result'):
                    with st.expander("Tool Result"):
                        st.text(details['result'])
            else:
                st.markdown(f"**ℹ️ [{timestamp}] {agent} - {activity_type.replace('_', ' ').title()}**")
                st.text(content)
                if details:
                    with st.expander("Details"):
                        st.json(details)
            
            st.divider()
            
    except Exception as e:
        st.error(f"Error displaying activity log: {e}")

st.set_page_config(page_title="CogniQuery", page_icon="🤖")
st.title("CogniQuery 🤖")
st.subheader("Your AI Data Scientist")

st.write(
    "Welcome to CogniQuery! Connect to your NeonDB database, ask a question in plain English, "
    "and receive a comprehensive report with charts and insights."
)

# --- User Inputs ---
st.sidebar.header("Configuration")
# Use blank inputs to hide secrets; fallback to .env defaults securely
openai_api_key = st.sidebar.text_input(
    "OpenAI API Key", 
    type="password", 
    value="",
    placeholder="Leave blank to use default key securely stored in .env"
)
db_connection_string = st.sidebar.text_input(
    "NeonDB Connection String",
    value="",
    placeholder="Leave blank to use default connection string from .env"
)

# --- Recommended Queries Section ---
st.header("💡 Recommended Queries")
st.write("*New to the dataset? Start with these sample questions to explore your data:*")

# Sample questions with engaging descriptions
sample_queries = [
    {
        "title": "🔍 Investigate Southeast Asia Profit Issues",
        "description": "Identify regional performance problems and root cause",
        "query": "Our profit in Southeast Asia is a disaster. Find the top 3 sub-categories that are losing the most money in that region. Show me their total sales and profit, and investigate if high discounts are the cause. Show with visualizations"
    },
    {
        "title": "💰 Discount Impact Analysis",
        "description": "Understand how the discounts affect bottom line",
        "query": "Show me the relationship between discount levels and profitability with visualization. Are high discounts killing our margins? Create a chart showing profit vs discount percentage."
    }
]

# Display sample queries in a nice grid
cols = st.columns(2)
for i, sample in enumerate(sample_queries):
    with cols[i % 2]:
        with st.container():
            st.markdown(f"**{sample['title']}**")
            st.caption(sample['description'])
            if st.button(f"Use This Query", key=f"sample_{i}", use_container_width=True):
                st.session_state.selected_query = sample['query']

st.header("🤖 Ask Your Data a Question")

# Use selected query if available
default_query = st.session_state.get('selected_query', '')
query = st.text_area(
    "Enter your question here:",
    value=default_query,
    placeholder="e.g., 'What were our total sales per month for the last year?'",
    height=150,
)


# Initialize session state for button control
if 'report_generating' not in st.session_state:
    st.session_state.report_generating = False

# Generate Report button with conditional disable
generate_button_disabled = st.session_state.report_generating
button_text = "⏳ Generating Report..." if st.session_state.report_generating else "Generate Report"

if st.button(button_text, disabled=generate_button_disabled):
    # Set the generating state to True
    st.session_state.report_generating = True
    
    # Use user inputs or fall back to environment variables
    final_openai_key = openai_api_key.strip() or os.getenv("OPENAI_API_KEY", "")
    final_db_conn = db_connection_string.strip() or os.getenv("NEONDB_CONN_STR", "")
    
    if not final_openai_key or not final_db_conn or not query:
        st.error("Please provide all required inputs: OpenAI Key, DB Connection String, and your query.")
        # Reset the generating state if there's an error
        st.session_state.report_generating = False
    else:
        # Set the API key for the current process
        os.environ["OPENAI_API_KEY"] = final_openai_key
        os.environ["NEONDB_CONN_STR"] = final_db_conn
        
        # Clean up old files before running
        cleanup_output_files()

        # Create placeholder for activity log
        activity_placeholder = st.empty()
        status_placeholder = st.empty()

        with status_placeholder:
            st.info("🤖 Your AI Data Scientist is starting up...")

        try:
            # Initialize and run the crew
            cogniquery_crew = CogniQueryCrew(db_connection_string=final_db_conn)
            
            # Run the crew in a separate process while updating the UI
            import threading
            result = [None]  # Use list to allow modification in nested function
            error = [None]
            
            def run_crew():
                try:
                    result[0] = cogniquery_crew.crew().kickoff(inputs={'query': query})
                except Exception as e:
                    error[0] = e
            
            # Start crew execution in background
            crew_thread = threading.Thread(target=run_crew)
            crew_thread.start()
            
            # Update activity log while crew is running
            while crew_thread.is_alive():
                with activity_placeholder.container():
                    display_activity_log()
                time.sleep(2)  # Update every 2 seconds
                
            # Wait for thread to complete
            crew_thread.join()
            
            # Final update of activity log
            with activity_placeholder.container():
                display_activity_log()
            
            if error[0]:
                raise error[0]
                
            with status_placeholder:
                st.success("✅ Report generated successfully!")
            
            # Reset the generating state on success
            st.session_state.report_generating = False

            # Display the generated markdown report
            st.subheader("📊 Generated Analysis Report")
            st.markdown(result[0].raw, unsafe_allow_html=True)
            
            # Display all chart images with improved detection
            output_dir = "output"
            chart_files = []
            
            # Debug: List all files in output directory
            try:
                if os.path.exists(output_dir):
                    output_files = os.listdir(output_dir)
                    chart_files = [f for f in output_files if f.endswith('.png')]
                    st.write(f"📁 Files in output directory: {output_files}")
                    st.write(f"📊 Chart files found: {chart_files}")
                else:
                    st.write("📁 Output directory does not exist")
            except Exception as e:
                st.write(f"📁 Could not list output directory: {e}")
            
            # Display charts
            if chart_files:
                st.subheader("📈 Generated Charts")
                
                # Sort chart files for consistent display order
                chart_files.sort()
                
                # Display each chart
                for i, chart_file in enumerate(chart_files):
                    chart_path = os.path.join(output_dir, chart_file)
                    try:
                        # Create a more descriptive caption
                        chart_name = chart_file.replace('.png', '').replace('_', ' ').title()
                        st.image(chart_path, caption=f"{chart_name}", use_container_width=True)
                        
                        # Add some spacing between charts
                        if i < len(chart_files) - 1:
                            st.write("")
                            
                    except Exception as e:
                        st.error(f"❌ Error displaying chart {chart_file}: {e}")
                
                st.success(f"✅ {len(chart_files)} chart(s) displayed successfully!")
                
            else:
                st.warning("⚠️ No charts were generated or could not be found. Check the activity log for details.")
                st.write(f"Expected charts location: {os.path.abspath(output_dir)}")
                if os.path.exists(output_dir):
                    output_contents = os.listdir(output_dir)
                    st.write(f"Output directory contents: {output_contents}")
                else:
                    st.write("Output directory does not exist")

            # --- ADD PDF DOWNLOAD SECTION ---
            st.divider()
            st.subheader("📄 Download Report")

            if result[0] and (WEASYPRINT_AVAILABLE or REPORTLAB_AVAILABLE):
                # Determine which PDF engine is being used
                pdf_engine = "WeasyPrint" if WEASYPRINT_AVAILABLE else "ReportLab"
                
                # Generate the PDF in memory
                with st.spinner(f"Creating PDF report using {pdf_engine}..."):
                    pdf_bytes = create_pdf_report(result[0].raw, chart_files)
                
                if pdf_bytes:
                    # Create different button text based on whether charts are included
                    button_text = "📥 Download Report with Charts as PDF" if chart_files else "📥 Download Report as PDF"
                    st.download_button(
                        label=button_text,
                        data=pdf_bytes,
                        file_name="CogniQuery_Analysis_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    success_msg = f"✅ PDF report with {len(chart_files)} embedded chart(s) is ready for download!" if chart_files else "✅ PDF report is ready for download!"
                    st.success(success_msg)
                    st.info(f"📝 Generated using {pdf_engine} PDF engine")
                else:
                    st.error("❌ Failed to generate PDF report.")
            elif not (WEASYPRINT_AVAILABLE or REPORTLAB_AVAILABLE):
                st.info("📄 PDF download feature requires either WeasyPrint or ReportLab library. Please check your environment setup.")
            else:
                st.info("📄 A report must be generated first to create a PDF.")
            # --- END OF PDF DOWNLOAD SECTION ---

        except Exception as e:
            with status_placeholder:
                st.error(f"❌ An error occurred: {e}")
            # Reset the generating state on error
            st.session_state.report_generating = False
        finally:
            # Ensure the generating state is reset
            st.session_state.report_generating = False
            # Keep the activity log visible after completion
            pass

st.sidebar.info(
    "**How it works:**\n"
    "1. **Business Analyst:** Refines your query and explores database schema.\n"
    "2. **Data Scientist:** Writes SQL queries, analyzes data, and creates charts.\n"
    "3. **Communications Strategist:** Compiles the final report.\n\n"
    "**🔍 Activity Log:** Watch the agents work in real-time! "
    "You'll see all SQL queries, tool usage, and progress updates as they happen.\n\n"
    "**💡 Configuration:** API keys and DB connection can be set in .env file "
    "or entered above. Values entered above will override .env settings."
)
