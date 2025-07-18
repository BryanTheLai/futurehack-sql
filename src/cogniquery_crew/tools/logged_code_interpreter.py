# src/cogniquery_crew/tools/logged_code_interpreter.py

from crewai_tools import CodeInterpreterTool
from .activity_logger import get_activity_logger

class LoggedCodeInterpreterTool(CodeInterpreterTool):
    """Code interpreter tool that logs Python code execution."""
    
    def __init__(self):
        super().__init__()
        self._last_logged_code = None
        
    def _run(self, **kwargs) -> str:
        """Override the run method to log code execution."""
        logger = get_activity_logger()
        
        # Extract code from kwargs
        code = kwargs.get('code', '')
        libraries_used = kwargs.get('libraries_used', [])
        
        # Avoid logging duplicate code executions
        if code and code != self._last_logged_code:
            details = {"tool": "Code Interpreter"}
            if libraries_used:
                details["libraries"] = libraries_used
                
            logger.log_activity(
                agent_name="Data Scientist",
                activity_type="python_code",
                content=code,
                details=details
            )
            self._last_logged_code = code
        
        # Execute the original code with all kwargs
        result = super()._run(**kwargs)
        
        # Check if chart was generated and provide detailed file system info
        import os
        chart_path = "output/chart.png"
        chart_exists = os.path.exists(chart_path)
        
        # Get file system details
        file_details = []
        try:
            if os.path.exists("output"):
                output_files = os.listdir("output")
                file_details.append(f"Files in output/: {output_files}")
            else:
                file_details.append("output/ directory does not exist")
                
            if chart_exists:
                chart_size = os.path.getsize(chart_path)
                file_details.append(f"Chart file size: {chart_size} bytes")
            
            current_dir = os.getcwd()
            file_details.append(f"Current working directory: {current_dir}")
            
        except Exception as e:
            file_details.append(f"File system check error: {e}")
        
        chart_status = "Chart saved successfully" if chart_exists else "Chart not found after execution"
        detailed_status = f"{chart_status}. {' | '.join(file_details)}"
        
        # Log the result (truncated for readability)
        result_preview = result[:300] + "..." if len(result) > 300 else result
        logger.log_tool_usage(
            agent_name="Data Scientist",
            tool_name="Code Interpreter",
            action=f"Python code execution completed - {detailed_status}",
            result=result_preview
        )
        
        return result
