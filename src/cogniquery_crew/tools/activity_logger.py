# src/cogniquery_crew/tools/activity_logger.py

import os
import json
import datetime
from typing import List, Dict, Any
import threading

class ActivityLogger:
    """Thread-safe activity logger for tracking agent activities and SQL queries."""
    
    def __init__(self, log_file_path: str = "output/activity_log.json"):
        self.log_file_path = log_file_path
        self.activities: List[Dict[str, Any]] = []
        self.current_agent: str = None
        self.current_task: str = None
        self._lock = threading.Lock()
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        
        # Initialize log file
        self._save_to_file()
    
    def log_activity(self, agent_name: str, activity_type: str, content: str, details: Dict[str, Any] = None):
        """Log an activity with timestamp."""
        with self._lock:
            activity = {
                "timestamp": datetime.datetime.now().isoformat(),
                "agent": agent_name,
                "type": activity_type,
                "content": content,
                "details": details or {}
            }
            self.activities.append(activity)
            self._save_to_file()
    
    def log_sql_query(self, agent_name: str, sql_query: str, result_preview: str = None):
        """Log an SQL query execution."""
        details = {}
        if result_preview:
            details["result_preview"] = result_preview[:500] + "..." if len(result_preview) > 500 else result_preview
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="sql_query",
            content=sql_query,
            details=details
        )
    
    def log_task_start(self, agent_name: str, task_name: str, description: str):
        """Log the start of a task."""
        with self._lock:
            self.current_agent = agent_name
            self.current_task = task_name
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="task_start",
            content=f"Starting task: {task_name}",
            details={"task_name": task_name, "description": description}
        )
    
    def log_task_complete(self, agent_name: str, task_name: str, output: str):
        """Log the completion of a task."""
        with self._lock:
            if self.current_task == task_name:
                self.current_agent = None
                self.current_task = None
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="task_complete",
            content=f"Completed task: {task_name}",
            details={"task_name": task_name, "output": output[:200] + "..." if len(output) > 200 else output}
        )
    
    def log_tool_usage(self, agent_name: str, tool_name: str, action: str, result: str = None):
        """Log tool usage."""
        details = {"tool_name": tool_name, "action": action}
        if result:
            details["result"] = result[:200] + "..." if len(result) > 200 else result
        
        self.log_activity(
            agent_name=agent_name,
            activity_type="tool_usage",
            content=f"Used {tool_name}: {action}",
            details=details
        )
    
    def get_current_status(self) -> Dict[str, str]:
        """Get the current agent and task status."""
        with self._lock:
            return {
                "current_agent": self.current_agent,
                "current_task": self.current_task
            }
    
    def get_activities(self) -> List[Dict[str, Any]]:
        """Get all logged activities."""
        with self._lock:
            return self.activities.copy()
    
    def clear_log(self):
        """Clear all activities."""
        with self._lock:
            self.activities = []
            self.current_agent = None
            self.current_task = None
            self._save_to_file()
    
    def _save_to_file(self):
        """Save activities to JSON file."""
        try:
            with open(self.log_file_path, 'w') as f:
                json.dump(self.activities, f, indent=2)
        except Exception as e:
            print(f"Error saving activity log: {e}")

# Global logger instance
_logger_instance = None

def get_activity_logger() -> ActivityLogger:
    """Get the global activity logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ActivityLogger()
    return _logger_instance
