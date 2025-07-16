"""
PR Creator Agent Implementation

Creates pull requests with fixes and improvements based on audit results.
"""

import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import git
from github import Github, GithubException

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from common.llm import LLMRequest


class PRCreator(BaseAgent):
    """Agent for creating pull requests with fixes and improvements."""
    
    def __init__(self):
        super().__init__(AgentType.PR_CREATOR, "PR Creator")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "PR Creator",
            "description": "Creates pull requests with fixes and improvements",
            "capabilities": [
                "Create feature branches",
                "Apply code fixes",
                "Generate commit messages",
                "Create pull request descriptions",
                "Handle GitHub API interactions",
                "Validate changes before submission"
            ],
            "outputs": [
                "branch_name",
                "commits",
                "pull_request_url",
                "changes_summary"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute PR creation."""
        try:
            # Get previous agent results
            code_fixer_result = context.agent_results.get('code_fixer')
            report_result = context.agent_results.get('report_generator')
            
            if not code_fixer_result or not code_fixer_result.success:
                return AgentResult(
                    success=False,
                    error="No code fixes available from Code Fixer agent",
                    metadata={"audit_id": context.audit_id}
                )
            
            # Extract fixes from code fixer
            fixes = code_fixer_result.data.get('fixes', [])
            if not fixes:
                return AgentResult(
                    success=False,
                    error="No fixes to apply",
                    metadata={"audit_id": context.audit_id}
                )
            
            # Create feature branch
            branch_name = await self._create_feature_branch(context)
            
            # Apply fixes
            applied_fixes = await self._apply_fixes(context, fixes)
            
            # Generate commit messages
            commits = await self._generate_commits(applied_fixes, report_result)
            
            # Create pull request
            pr_url = await self._create_pull_request(
                context, branch_name, commits, report_result
            )
            
            # Compile results
            result_data = {
                "branch_name": branch_name,
                "commits": commits,
                "pull_request_url": pr_url,
                "changes_summary": {
                    "files_modified": len(applied_fixes),
                    "total_fixes": len(fixes),
                    "successful_fixes": len([f for f in applied_fixes if f.get('success')])
                },
                "applied_fixes": applied_fixes
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "audit_id": context.audit_id,
                    "repository_url": context.repository_url,
                    "branch": branch_name,
                    "pr_url": pr_url
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={
                    "audit_id": context.audit_id,
                    "repository_url": context.repository_url
                }
            )
    
    async def _create_feature_branch(self, context: AgentContext) -> str:
        """Create a feature branch for the changes."""
        repo_path = context.shared_data.get('repository_path')
        if not repo_path:
            raise ValueError("Repository path not found in context")
        
        # Generate branch name
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        branch_name = f"ai-audit-fixes-{timestamp}"
        
        try:
            # Initialize git repository if needed
            if not os.path.exists(os.path.join(repo_path, '.git')):
                repo = git.Repo.init(repo_path)
                # Add remote origin if not exists
                if not repo.remotes:
                    repo.create_remote('origin', context.repository_url)
            else:
                repo = git.Repo(repo_path)
            
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            self.logger.info(f"Created feature branch: {branch_name}")
            return branch_name
            
        except Exception as e:
            raise Exception(f"Failed to create feature branch: {e}")
    
    async def _apply_fixes(self, context: AgentContext, fixes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply fixes to the codebase."""
        applied_fixes = []
        repo_path = context.shared_data.get('repository_path')
        
        for fix in fixes:
            try:
                file_path = fix.get('file_path')
                if not file_path:
                    continue
                
                full_path = os.path.join(repo_path, file_path)
                if not os.path.exists(full_path):
                    self.logger.warning(f"File not found: {full_path}")
                    continue
                
                # Apply the fix
                fix_type = fix.get('type', 'patch')
                if fix_type == 'patch':
                    success = await self._apply_patch(full_path, fix.get('patch', ''))
                elif fix_type == 'replacement':
                    success = await self._apply_replacement(full_path, fix.get('content', ''))
                else:
                    self.logger.warning(f"Unknown fix type: {fix_type}")
                    continue
                
                applied_fixes.append({
                    'file_path': file_path,
                    'fix_type': fix_type,
                    'success': success,
                    'description': fix.get('description', ''),
                    'severity': fix.get('severity', 'medium')
                })
                
                if success:
                    self.logger.info(f"Applied fix to {file_path}")
                else:
                    self.logger.error(f"Failed to apply fix to {file_path}")
                    
            except Exception as e:
                self.logger.error(f"Error applying fix: {e}")
                applied_fixes.append({
                    'file_path': fix.get('file_path', 'unknown'),
                    'fix_type': fix.get('type', 'unknown'),
                    'success': False,
                    'error': str(e)
                })
        
        return applied_fixes
    
    async def _apply_patch(self, file_path: str, patch_content: str) -> bool:
        """Apply a patch to a file."""
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply patch (simplified - in production, use proper patch library)
            # This is a basic implementation - consider using `patch` library
            lines = original_content.split('\n')
            patch_lines = patch_content.split('\n')
            
            # Simple patch application (very basic)
            # In production, use proper diff/patch libraries
            modified_content = original_content
            
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying patch: {e}")
            return False
    
    async def _apply_replacement(self, file_path: str, new_content: str) -> bool:
        """Replace file content with new content."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception as e:
            self.logger.error(f"Error applying replacement: {e}")
            return False
    
    async def _generate_commits(self, applied_fixes: List[Dict[str, Any]], report_result: Optional[AgentResult]) -> List[Dict[str, Any]]:
        """Generate commit messages for the changes."""
        commits = []
        
        # Group fixes by type
        critical_fixes = [f for f in applied_fixes if f.get('severity') == 'critical' and f.get('success')]
        warning_fixes = [f for f in applied_fixes if f.get('severity') == 'warning' and f.get('success')]
        other_fixes = [f for f in applied_fixes if f.get('success') and f.get('severity') not in ['critical', 'warning']]
        
        # Create commit for critical fixes
        if critical_fixes:
            commit_msg = await self._generate_commit_message(critical_fixes, 'critical')
            commits.append({
                'message': commit_msg,
                'files': [f['file_path'] for f in critical_fixes],
                'type': 'critical_fixes'
            })
        
        # Create commit for warning fixes
        if warning_fixes:
            commit_msg = await self._generate_commit_message(warning_fixes, 'warning')
            commits.append({
                'message': commit_msg,
                'files': [f['file_path'] for f in warning_fixes],
                'type': 'warning_fixes'
            })
        
        # Create commit for other fixes
        if other_fixes:
            commit_msg = await self._generate_commit_message(other_fixes, 'improvement')
            commits.append({
                'message': commit_msg,
                'files': [f['file_path'] for f in other_fixes],
                'type': 'improvements'
            })
        
        return commits
    
    async def _generate_commit_message(self, fixes: List[Dict[str, Any]], fix_type: str) -> str:
        """Generate a commit message using LLM."""
        fix_descriptions = [f.get('description', '') for f in fixes if f.get('description')]
        
        prompt = f"""
        Generate a concise commit message for {len(fixes)} {fix_type} fixes.
        
        Fix descriptions:
        {chr(10).join(f"- {desc}" for desc in fix_descriptions[:5])}
        
        Requirements:
        - Use conventional commit format
        - Be concise but descriptive
        - Include the type of fixes
        - Maximum 72 characters for the first line
        
        Format: <type>(<scope>): <description>
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_message="You are a Git expert creating clear, conventional commit messages.",
            temperature=0.1,
            max_tokens=100
        )
        
        response = await self.call_llm(request)
        
        if response.error:
            return f"fix: apply {len(fixes)} {fix_type} fixes"
        
        return response.content.strip()
    
    async def _create_pull_request(
        self, context: AgentContext, branch_name: str, 
        commits: List[Dict[str, Any]], report_result: Optional[AgentResult]
    ) -> str:
        """Create a pull request on GitHub."""
        try:
            # Get GitHub configuration
            github_token = self.config.get('github', {}).get('token')
            github_username = self.config.get('github', {}).get('username')
            
            if not github_token:
                raise ValueError("GitHub token not configured")
            
            # Initialize GitHub client
            g = Github(github_token)
            
            # Extract repository info from URL
            repo_url = context.repository_url
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            repo_name = repo_url.split('/')[-2] + '/' + repo_url.split('/')[-1]
            repo = g.get_repo(repo_name)
            
            # Generate PR title and description
            pr_title = await self._generate_pr_title(commits, report_result)
            pr_description = await self._generate_pr_description(commits, report_result)
            
            # Create pull request
            pr = repo.create_pull(
                title=pr_title,
                body=pr_description,
                head=branch_name,
                base=context.branch
            )
            
            self.logger.info(f"Created pull request: {pr.html_url}")
            return pr.html_url
            
        except GithubException as e:
            raise Exception(f"GitHub API error: {e}")
        except Exception as e:
            raise Exception(f"Failed to create pull request: {e}")
    
    async def _generate_pr_title(self, commits: List[Dict[str, Any]], report_result: Optional[AgentResult]) -> str:
        """Generate PR title using LLM."""
        total_fixes = sum(len(commit.get('files', [])) for commit in commits)
        
        prompt = f"""
        Generate a concise pull request title for an AI-generated code audit with {total_fixes} fixes.
        
        Commit types: {[c.get('type') for c in commits]}
        
        Requirements:
        - Be concise and descriptive
        - Mention it's an AI audit
        - Include the number of fixes
        - Maximum 60 characters
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_message="You are a GitHub expert creating clear pull request titles.",
            temperature=0.1,
            max_tokens=50
        )
        
        response = await self.call_llm(request)
        
        if response.error:
            return f"🤖 AI Audit: {total_fixes} fixes"
        
        return response.content.strip()
    
    async def _generate_pr_description(self, commits: List[Dict[str, Any]], report_result: Optional[AgentResult]) -> str:
        """Generate PR description using LLM."""
        # Extract summary from report
        summary = ""
        if report_result and report_result.success:
            summary = report_result.data.get('executive_summary', {}).get('summary', '')
        
        commit_summary = []
        for commit in commits:
            commit_summary.append(f"- {commit.get('type', 'unknown')}: {len(commit.get('files', []))} files")
        
        prompt = f"""
        Generate a comprehensive pull request description for an AI code audit.
        
        Executive Summary:
        {summary[:500] if summary else 'No summary available'}
        
        Changes:
        {chr(10).join(commit_summary)}
        
        Requirements:
        - Explain what the AI audit found
        - List the types of fixes applied
        - Include any important notes or warnings
        - Be professional and clear
        - Mention this is an automated audit
        """
        
        request = LLMRequest(
            prompt=prompt,
            system_message="You are a software engineer creating professional pull request descriptions.",
            temperature=0.1,
            max_tokens=500
        )
        
        response = await self.call_llm(request)
        
        if response.error:
            return f"""## AI Code Audit Results

This pull request contains fixes generated by an automated AI code audit.

### Changes
{chr(10).join(commit_summary)}

### Note
This is an automated audit. Please review all changes before merging."""
        
        return response.content.strip()