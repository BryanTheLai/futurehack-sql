# src/cogniquery_crew/tools/local_code_executor.py

import os
import sys
import subprocess
import tempfile
from crewai.tools import BaseTool
from .activity_logger import get_activity_logger

class LocalCodeExecutorTool(BaseTool):
    """Local code executor tool that runs Python code in the current environment.
    
    This tool executes Python code locally instead of in a Docker container,
    ensuring access to all installed packages like matplotlib.
    """
    
    name: str = "LocalCodeExecutor"
    description: str = """MANDATORY: Execute Python code for data analysis and chart creation after EVERY SQL query.
    
    ⚠️  CRITICAL REQUIREMENT: This tool MUST be used to create charts and perform data analysis with Python.
    ⚠️  WITHOUT THIS TOOL, NO CHARTS WILL BE GENERATED OR DISPLAYED IN THE UI.
    
    WORKFLOW REQUIREMENT:
    1. Get data with SQLExecutor
    2. IMMEDIATELY use LocalCodeExecutor to create charts with that data
    3. Save charts with plt.savefig() - this is the ONLY way charts appear in the UI
    
    Parameters:
    - code: Python code to execute (required)
    
    CHART REQUIREMENTS (MANDATORY):
    - Use matplotlib.pyplot for visualizations: import matplotlib.pyplot as plt
    - Save charts to output directory: plt.savefig('output/chart_1.png')
    - Create as many charts as needed for comprehensive analysis
    - Charts are automatically displayed in the Streamlit UI ONLY if saved with plt.savefig()
    
    DATA INPUT PATTERN:
    - SQL results are typically provided as CSV strings
    - Use pd.read_csv(io.StringIO(csv_data)) to convert CSV strings to DataFrames
    - Always validate data before creating charts
    
    AVAILABLE LIBRARIES: pandas, numpy, matplotlib, datetime, json, re, io
    
    ⚠️  REMINDER: Without LocalCodeExecutor + plt.savefig(), NO CHARTS will appear in the UI!"""
    
    def __init__(self):
        super().__init__()
        
    def _run(self, code: str = None, **kwargs) -> str:
        """Run Python code locally and log the execution."""
        # Add debugging
        print(f"🐛 DEBUG: LocalCodeExecutor._run called with code={code is not None}, kwargs: {list(kwargs.keys())}")
        # Handle both calling patterns
        if code is None:
            code = kwargs.get('code', '')
        return self._execute_code(code=code, **kwargs)
    
    def run(self, **kwargs) -> str:
        """Alternative method name that some CrewAI versions might use."""
        print(f"🐛 DEBUG: LocalCodeExecutor.run called with kwargs: {list(kwargs.keys())}")
        return self._execute_code(**kwargs)
    
    def execute(self, **kwargs) -> str:
        """Another alternative method name."""
        print(f"🐛 DEBUG: LocalCodeExecutor.execute called with kwargs: {list(kwargs.keys())}")
        return self._execute_code(**kwargs)
    
    def _execute_code(self, code: str = None, **kwargs) -> str:
        """The actual implementation - all methods delegate to this."""
        # Add debugging
        print(f"🐛 DEBUG: LocalCodeExecutor._execute_code called with code={code is not None}, kwargs: {list(kwargs.keys())}")
        
        logger = get_activity_logger()
        
        # Extract code from kwargs if not provided directly
        if not code:
            code = kwargs.get('code', '')
        if not code:
            print("🐛 DEBUG: No code provided to LocalCodeExecutor")
            return "Error: No code provided to execute"
        
        print(f"🐛 DEBUG: Code to execute: {code[:100]}...")
        
        libraries_used = kwargs.get('libraries_used', [])
        
        # Check for problematic library usage and provide helpful guidance
        code = self._check_and_fix_common_issues(code)
        
        # Enhance code with reliable chart generation setup
        if 'plt.savefig' in code and 'output/' in code:
            # Inject reliable chart generation code
            enhanced_code = self._enhance_chart_code(code)
            code = enhanced_code
            print("🐛 DEBUG: Enhanced code with chart generation setup")
        
        # Avoid logging duplicate code executions
        if not hasattr(LocalCodeExecutorTool, '_last_logged_code'):
            LocalCodeExecutorTool._last_logged_code = None
            
        # Always log LocalCodeExecutor usage for debugging
        details = {"tool": "LocalCodeExecutor"}
        if libraries_used:
            details["libraries"] = libraries_used
            
        print("🐛 DEBUG: About to log activity...")
        logger.log_activity(
            agent_name="Data Scientist",
            activity_type="python_code",
            content=code[:500] + "..." if len(code) > 500 else code,
            details=details
        )
        print("🐛 DEBUG: Activity logged successfully")
        
        LocalCodeExecutorTool._last_logged_code = code
        
        # Execute code locally
        try:
            print("🐛 DEBUG: About to execute code locally...")
            result = self._execute_locally(code)
            print(f"🐛 DEBUG: Code execution result: {result[:200]}...")
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            print(f"🐛 DEBUG: Error executing code: {e}")
            logger.log_activity(
                agent_name="Data Scientist",
                activity_type="python_code",
                content=f"ERROR: {error_msg}",
                details={"error": str(e)}
            )
            return error_msg
        
        # Execute code locally
        try:
            result = self._execute_locally(code)
            return result
        except Exception as e:
            error_msg = f"Error executing code: {str(e)}"
            logger.log_activity(
                agent_name="Data Scientist",
                activity_type="python_code",
                content=f"ERROR: {error_msg}",
                details={"error": str(e)}
            )
            return error_msg

    def _execute_locally(self, code: str) -> str:
        """Execute Python code in the local environment."""
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Execute the code using the current Python interpreter
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=os.getcwd(),
                timeout=30,  # 30 second timeout
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}  # Force UTF-8 encoding
            )
            
            if result.returncode == 0:
                output = result.stdout
                if result.stderr:
                    output += f"\\nWarnings: {result.stderr}"
                
                # Check if any chart files were created
                chart_files = []
                if os.path.exists("output"):
                    for file in os.listdir("output"):
                        if file.endswith('.png'):
                            chart_files.append(file)
                
                if chart_files:
                    output += f"\\n\\nCharts created: {', '.join(chart_files)}"
                else:
                    output += "\\n\\nNo chart files were created in output directory"
                    
                return output or "Code executed successfully (no output)"
            else:
                error_output = f"Code execution failed:\\nReturn code: {result.returncode}\\nStdout: {result.stdout}\\nStderr: {result.stderr}"
                return error_output
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def _check_and_fix_common_issues(self, code: str) -> str:
        """Check for common issues and provide fixes or alternatives."""
        
        # Check for df.to_markdown() usage which requires tabulate
        if 'to_markdown(' in code:
            replacement_code = code.replace('df.to_markdown()', 'df.to_string()')
            return replacement_code
        
        # Check for other problematic imports
        problematic_imports = [
            ('import seaborn', 'seaborn is not available. Use matplotlib instead.'),
            ('import plotly', 'plotly is not available. Use matplotlib instead.'),
            ('import bokeh', 'bokeh is not available. Use matplotlib instead.'),
            ('import altair', 'altair is not available. Use matplotlib instead.'),
            ('from tabulate', 'tabulate is not available. Use manual table formatting.'),
        ]
        
        for problematic, suggestion in problematic_imports:
            if problematic in code:
                return f"# Error: {suggestion}\\n# Please rewrite your code without {problematic.split()[1]}\\n{code}"
        
        return code

    def _enhance_chart_code(self, original_code: str) -> str:
        """Enhance code to ensure reliable chart generation."""
        enhancement_prefix = '''
# === CHART GENERATION RELIABILITY ENHANCEMENTS ===
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import io
import os

# Ensure output directory exists
os.makedirs('output', exist_ok=True)

# Clear any existing matplotlib state
plt.clf()
plt.close('all')

'''
        
        enhancement_suffix = '''

# === CHART SAVING WITH VERIFICATION ===
print("Chart generation code completed")

'''
        
        return enhancement_prefix + original_code + enhancement_suffix
