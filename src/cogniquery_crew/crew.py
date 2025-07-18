# src/cogniquery_crew/crew.py

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import CodeInterpreterTool

from .tools.schema_explorer_tool import SchemaExplorerTool
from .tools.sample_data_tool import SampleDataTool
from .tools.sql_executor_tool import SQLExecutorTool
from .tools.reporting_tools import ReportingTools
from .tools.activity_logger import get_activity_logger

# Set up the default LLM
os.environ["OPENAI_MODEL_NAME"] = "gpt-4.1"

# Base directory for configuration files
BASE_DIR = os.path.dirname(__file__)

@CrewBase
class CogniQueryCrew():
    """CogniQuery crew for data analysis and reporting."""
    # Configuration file paths
    agents_config = os.path.join(BASE_DIR, 'config', 'agents.yaml')
    tasks_config = os.path.join(BASE_DIR, 'config', 'tasks.yaml')

    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
        self.schema_tool = SchemaExplorerTool()
        self.sample_data_tool = SampleDataTool()
        self.sql_executor_tool = SQLExecutorTool()
        self.report_tool = ReportingTools()
        self.code_interpreter_tool = CodeInterpreterTool()
        
        # Configure all database tools with the connection string
        for tool in [self.schema_tool, self.sample_data_tool, self.sql_executor_tool]:
            if hasattr(tool, 'db_connection_string'):
                tool.db_connection_string = db_connection_string
        
        # Clear previous activity log
        logger = get_activity_logger()
        logger.clear_log()

    @agent
    def prompt_enhancer(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_enhancer'],
            tools=[self.schema_tool, self.sample_data_tool],
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[self.schema_tool, self.sample_data_tool, self.sql_executor_tool, self.code_interpreter_tool],
            verbose=True,
            allow_delegation=False
        )
    
    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'],
            verbose=True
        )

    @task
    def enhance_prompt_task(self) -> Task:
        logger = get_activity_logger()
        task_config = self.tasks_config['enhance_prompt_task']
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Business Analyst", "enhance_prompt_task", task_config['description'])
        
        return Task(
            config=task_config,
            agent=self.prompt_enhancer(),
            callbacks={'on_start': log_start_callback}
        )

    @task
    def analyze_data_task(self) -> Task:
        logger = get_activity_logger()
        # Notify agent that connection is auto-configured
        task_description = self.tasks_config['analyze_data_task']['description'] + "\n\nNOTE: The database connection is automatically configured. When using Database Tools, only provide the SQL query."
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Data Scientist", "analyze_data_task", task_description)
        
        return Task(
            config={
                'description': task_description,
                'expected_output': self.tasks_config['analyze_data_task']['expected_output']
            },
            agent=self.data_analyst(),
            context=[self.enhance_prompt_task()],  # Direct dependency on business analyst
            callbacks={'on_start': log_start_callback}
        )

    @task
    def generate_report_task(self) -> Task:
        logger = get_activity_logger()
        # Write the final markdown report to a file for later PDF conversion
        md_path = "output/final_report.md"
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Communications Strategist", "generate_report_task", self.tasks_config['generate_report_task']['description'])
        
        return Task(
            config=self.tasks_config['generate_report_task'],
            agent=self.report_generator(),
            context=[self.analyze_data_task()],
            output_file=md_path,
            callbacks={'on_start': log_start_callback}
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CogniQuery crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
