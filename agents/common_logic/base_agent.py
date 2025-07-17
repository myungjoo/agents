import requests
import time
import os
import json
import argparse
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Base class for all agents. Handles communication with the controller
    and the main work loop.
    """
    def __init__(self, name: str):
        self.name = name
        self.parser = argparse.ArgumentParser(description=f"{self.name} Agent")
        self.parser.add_argument("--controller-url", required=True, help="URL of the agent controller")
        self.args = self.parser.parse_args()
        self.controller_url = self.args.controller_url
        self.job_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs', f'{self.name}.job')


    def update_status(self, status: str, details: str):
        """Reports the agent's status back to the controller."""
        try:
            requests.post(
                f"{self.controller_url}/api/agents/{self.name}/status",
                json={"status": status, "details": details}
            )
            print(f"[{self.name}] Status Updated: {status} - {details}")
        except requests.exceptions.ConnectionError:
            print(f"[{self.name}] Error: Could not connect to controller to update status.")

    def check_for_job(self):
        """Checks for a new job file."""
        if os.path.exists(self.job_file_path):
            try:
                with open(self.job_file_path, 'r') as f:
                    job_data = json.load(f)
                os.remove(self.job_file_path) # Consume the job
                return job_data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[{self.name}] Error reading job file: {e}")
                os.remove(self.job_file_path)
        return None

    @abstractmethod
    def perform_task(self, job_data: dict):
        """The core logic of the agent, to be implemented by subclasses."""
        pass

    def run(self):
        """The main loop for the agent."""
        self.update_status("running", "Idle, waiting for job.")
        try:
            while True:
                job = self.check_for_job()
                if job:
                    self.update_status("working", f"Starting task for repo: {job.get('repo_url')}")
                    try:
                        self.perform_task(job)
                        self.update_status("running", "Task completed. Waiting for new job.")
                    except Exception as e:
                        error_message = f"An error occurred during task execution: {e}"
                        print(f"[{self.name}] {error_message}")
                        self.update_status("running", f"Error: {error_message}. Awaiting new job.")
                
                time.sleep(5) # Poll for new jobs every 5 seconds
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Agent shutting down.")
        finally:
            self.update_status("stopped", "Agent process terminated.")


