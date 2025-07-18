# src/cogniquery_crew/tools/logged_code_interpreter.py

import os
import matplotlib
from crewai_tools import CodeInterpreterTool
from .activity_logger import get_activity_logger

# Configure matplotlib to use Agg backend for server environments
matplotlib.use('Agg')

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
        
        # Enhance code with reliable chart generation setup
        if 'plt.savefig' in code and 'output/chart.png' in code:
            # Inject reliable chart generation code
            enhanced_code = self._enhance_chart_code(code)
            kwargs['code'] = enhanced_code
            code = enhanced_code
        
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
        
        # Check if chart was generated - simplified without os module
        try:
            import os
            chart_path = "output/chart.png"
            chart_exists = os.path.exists(chart_path)
            
            # Get file system details
            file_details = []
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
            
            chart_status = "Chart saved successfully" if chart_exists else "Chart not found after execution"
            detailed_status = f"{chart_status}. {' | '.join(file_details)}"
            
        except Exception as e:
            # Fallback if we can't check file system
            detailed_status = f"Chart generation attempted. File system check failed: {e}"
        
        # Log the result (truncated for readability)
        result_preview = result[:300] + "..." if len(result) > 300 else result
        logger.log_tool_usage(
            agent_name="Data Scientist",
            tool_name="Code Interpreter",
            action=f"Python code execution completed - {detailed_status}",
            result=result_preview
        )
        
        return result

    def _enhance_chart_code(self, original_code: str) -> str:
        """Enhance code to ensure reliable chart generation."""
        enhancement_prefix = '''
# === CHART GENERATION RELIABILITY ENHANCEMENTS ===
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

# Clear any existing matplotlib state
plt.clf()
plt.close('all')

'''
        
        enhancement_suffix = '''

# === CHART SAVING WITH VERIFICATION ===
try:
    plt.savefig('output/chart.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Chart successfully saved to output/chart.png")
        
except Exception as e:
    print(f"❌ Error saving chart: {e}")
    try:
        import traceback
        traceback.print_exc()
    except:
        pass

'''
        
        return enhancement_prefix + original_code + enhancement_suffix
