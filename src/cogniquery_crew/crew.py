# src/cogniquery_crew/crew.py

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import CodeInterpreterTool
from langchain_openai import ChatOpenAI

from .tools.db_tools import DatabaseTools
from .tools.reporting_tools import ReportingTools

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
        self.code_interpreter_tool = CodeInterpreterTool()

    @agent
    def prompt_enhancer(self) -> Agent:
        return Agent(
            config=self.agents_config['prompt_enhancer'],
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
        return Task(
            config=self.tasks_config['enhance_prompt_task'],
            agent=self.prompt_enhancer()
        )

    @task
    def generate_sql_task(self) -> Task:
        # Retrieve the current database schema to include in the prompt
        schema = self.db_tool.get_schema()
        orig = self.tasks_config['generate_sql_task']
        # Prepend schema to the task description
        description = orig['description'] + "\n\nDatabase Schema:\n" + schema + "\n\nNOTE: The database connection is automatically configured. When using Database Tools, only provide the SQL query - do not specify connection string parameters."
        return Task(
            config={
                'description': description,
                'expected_output': orig['expected_output']
            },
            agent=self.sql_generator(),
            context=[self.enhance_prompt_task()]
        )

    @task
    def analyze_data_task(self) -> Task:
        # Notify agent that connection is auto-configured
        task_description = self.tasks_config['analyze_data_task']['description'] + "\n\nNOTE: The database connection is automatically configured. When using Database Tools, only provide the SQL query."
        return Task(
            config={
                'description': task_description,
                'expected_output': self.tasks_config['analyze_data_task']['expected_output']
            },
            agent=self.data_analyst(),
            context=[self.generate_sql_task()]
        )

    @task
    def generate_report_task(self) -> Task:
        # Write the final markdown report to a file for later PDF conversion
        md_path = "output/final_report.md"
        return Task(
            config=self.tasks_config['generate_report_task'],
            agent=self.report_generator(),
            context=[self.analyze_data_task()],
            output_file=md_path
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
