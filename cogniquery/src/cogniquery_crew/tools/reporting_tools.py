# src/cogniquery_crew/tools/reporting_tools.py

import os
import base64
from crewai_tools import BaseTool
from weasyprint import HTML, CSS
from markdown_it import MarkdownIt

class ReportingTools(BaseTool):
    name: str = "Reporting Tools"
    description: str = "A tool to create a PDF report from markdown content."

    def create_report(self, markdown_content: str, report_file_path: str) -> str:
        """
        Converts markdown content, including images and tables, into a PDF report.
        It saves the report to the specified file path.
        """
        # Ensure the output directory exists
        output_dir = os.path.dirname(report_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Convert markdown to HTML
        md = MarkdownIt()
        html_content = md.render(markdown_content)

        # Basic CSS for styling
        css = CSS(string='''
            @page { size: A4; margin: 2cm; }
            body { font-family: sans-serif; line-height: 1.5; }
            h1, h2, h3 { color: #333; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 1em; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            img { max-width: 100%; height: auto; display: block; margin: 1em 0; }
        ''')

        # Create PDF
        try:
            HTML(string=html_content).write_pdf(report_file_path, stylesheets=[css])
            return f"Successfully created report at {report_file_path}"
        except Exception as e:
            return f"Error creating PDF report: {e}"
