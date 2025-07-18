# src/cogniquery_crew/crew.py

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import CodeInterpreterTool
from langchain_openai import ChatOpenAI

from .tools.db_tools import DatabaseTools
from .tools.reporting_tools import ReportingTools

# Set up the default LLM
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"

@CrewBase
class CogniQueryCrew():
    """CogniQuery crew for data analysis and reporting."""
    agents_config = 'src/cogniquery_crew/config/agents.yaml'
    tasks_config = 'src/cogniquery_crew/config/tasks.yaml'

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
            tools=[self.report_tool],
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
        return Task(
            config=self.tasks_config['generate_sql_task'],
            agent=self.sql_generator(),
            context=[self.enhance_prompt_task()]
        )

    @task
    def analyze_data_task(self) -> Task:
        # Pass the connection string to the task description for the agent to use
        task_description = self.tasks_config['analyze_data_task']['description']
        return Task(
            config={
                'description': task_description,
                'expected_output': self.tasks_config['analyze_data_task']['expected_output']
            },
            agent=self.data_analyst(),
            context=[self.generate_sql_task()],
            # Pass the connection string to the tool
            tools_context={'db_connection_string': self.db_connection_string}
        )

    @task
    def generate_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_report_task'],
            agent=self.report_generator(),
            context=[self.analyze_data_task()],
            output_file="output/final_report.md"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CogniQuery crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=2,
        )
