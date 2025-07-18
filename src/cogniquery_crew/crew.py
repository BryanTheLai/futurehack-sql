# src/cogniquery_crew/crew.py

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools.db_tools import DatabaseTools
from .tools.reporting_tools import ReportingTools
from .tools.logged_code_interpreter import LoggedCodeInterpreterTool
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
        self.db_tool = DatabaseTools()
        self.report_tool = ReportingTools()
        self.code_interpreter_tool = LoggedCodeInterpreterTool()
        
        # Clear previous activity log
        logger = get_activity_logger()
        logger.clear_log()

    @agent
    def prompt_enhancer(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_enhancer'],
            tools=[self.db_tool],
            verbose=True
        )

    @agent
    def sql_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['sql_generator'],
            tools=[self.db_tool],
            verbose=True
        )

    @agent
    def data_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst'],
            tools=[self.db_tool, self.code_interpreter_tool],
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
    def generate_sql_task(self) -> Task:
        logger = get_activity_logger()
        orig = self.tasks_config['generate_sql_task']
        # The Business Analyst will now provide schema-aware refined queries
        description = orig['description'] + "\n\nNOTE: The database connection is automatically configured. When using Database Tools, only provide the SQL query - do not specify connection string parameters. The refined question from the Business Analyst should already be schema-aware."
        
        # Log task start
        def log_start_callback(task):
            logger.log_task_start("Database Administrator", "generate_sql_task", description)
        
        return Task(
            config={
                'description': description,
                'expected_output': orig['expected_output']
            },
            agent=self.sql_generator(),
            context=[self.enhance_prompt_task()],
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
            context=[self.generate_sql_task()],
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
