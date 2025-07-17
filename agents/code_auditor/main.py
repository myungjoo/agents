import sys
import os
import time

# Add project root to path to allow imports from common
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.common_logic.base_agent import BaseAgent
from common.llm_providers import get_llm_provider

class CodeAuditorAgent(BaseAgent):
    """
    An agent that performs a multi-step audit of a software repository.
    """
    def __init__(self):
        super().__init__("code_auditor")
        self.llm = get_llm_provider()

    def perform_task(self, job_data: dict):
        """Orchestrates the code audit workflow."""
        repo_url = job_data.get("repo_url")
        if not repo_url:
            self.update_status("running", "Error: No repository URL provided in job.")
            return

        self.update_status("working", f"1/6: Cloning repository {repo_url}...")
        time.sleep(2) # Placeholder for actual git clone operation

        self.update_status("working", "2/6: Analyzing project structure...")
        analysis_prompt = f"Analyze the project structure of the code at {repo_url}. What is its purpose, main language, and build system? How would you test it?"
        structure_analysis = self.llm.generate_text(analysis_prompt)
        self.update_status("working", f"2/6: Analysis complete. Project seems to be: {structure_analysis[:100]}...")
        time.sleep(2)

        self.update_status("working", "3/6: Hunting for potential bugs...")
        bug_hunt_prompt = f"Based on this analysis, what are three potential high-impact bugs (correctness, memory, performance) to look for in the codebase at {repo_url}? Be specific."
        bug_ideas = self.llm.generate_text(bug_hunt_prompt)
        self.update_status("working", f"3/6: Bug hunt ideas generated.")
        time.sleep(2)

        self.update_status("working", "4/6: Writing issue report...")
        time.sleep(2)

        self.update_status("working", "5/6: Proposing code fixes as commits...")
        time.sleep(2)

        self.update_status("working", "6/6: Creating pull request...")
        time.sleep(2)

        final_report = f"Audit of {repo_url} complete. Found potential issues and created a mock pull request."
        print(f"[{self.name}] {final_report}")
        # In a real implementation, this would be much more detailed.

if __name__ == "__main__":
    agent = CodeAuditorAgent()
    agent.run()

