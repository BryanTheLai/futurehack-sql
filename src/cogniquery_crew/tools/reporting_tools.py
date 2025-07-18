# src/cogniquery_crew/tools/reporting_tools.py

import os
import base64
from crewai.tools import BaseTool
from markdown_it import MarkdownIt
from .activity_logger import get_activity_logger

class ReportingTools(BaseTool):
    name: str = "Reporting Tools"
    description: str = "A tool to create a PDF report from markdown content."

    def create_report(self, markdown_content: str, report_file_path: str) -> str:
        """
        Converts markdown content, including images and tables, into a PDF report.
        It saves the report to the specified file path.
        """
        logger = get_activity_logger()
        logger.log_tool_usage("Communications Strategist", "Reporting Tools", f"Creating PDF report at {report_file_path}")
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(report_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Convert markdown to HTML
        md = MarkdownIt()
        html_content = md.render(markdown_content)

        # Import WeasyPrint here to catch missing native dependencies
        try:
            from weasyprint import HTML, CSS
        except (ImportError, OSError) as e:
            error_msg = f"WeasyPrint import error: {e}. Please install WeasyPrint and its native dependencies as per https://doc.courtbouillon.org/weasyprint/stable/first_steps.html."
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", f"PDF creation failed: {error_msg}")
            return error_msg

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
            success_msg = f"Successfully created report at {report_file_path}"
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", success_msg)
            return success_msg
        except Exception as e:
            error_msg = f"Error creating PDF report: {e}"
            logger.log_tool_usage("Communications Strategist", "Reporting Tools", error_msg)
            return error_msg

    def _run(self, markdown_content: str, report_file_path: str = None, **kwargs) -> str:
        """
        Abstract method implementation for BaseTool. Calls create_report.
        """
        # Get report file path from kwargs if not provided directly
        if not report_file_path and 'report_file_path' in kwargs:
            report_file_path = kwargs['report_file_path']
        
        if not report_file_path:
            return "Error: No report file path provided"
            
        return self.create_report(markdown_content, report_file_path)
