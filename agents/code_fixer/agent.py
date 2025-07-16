"""
Code Fixer Agent Implementation

Generates fixes for detected issues and creates patches for code improvements.
"""

import os
import json
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from common.llm import LLMRequest


class CodeFixer(BaseAgent):
    """Agent for generating code fixes."""
    
    def __init__(self):
        super().__init__(AgentType.CODE_FIXER, "Code Fixer")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "Code Fixer",
            "description": "Generates fixes for detected issues",
            "capabilities": [
                "Issue-based fix generation",
                "Code patch creation",
                "Fix validation",
                "Multiple fix strategies"
            ],
            "supported_languages": ["c", "cpp", "python", "java", "javascript", "typescript", "go", "rust"],
            "outputs": [
                "fixes",
                "patches",
                "fix_metadata"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute code fixing."""
        try:
            # Get issue detection results
            issue_analysis = context.agent_results.get('issue_detector')
            if not issue_analysis or not issue_analysis.success:
                raise Exception("Issue analysis not available")
            
            issues = issue_analysis.data.get('issues', [])
            if not issues:
                return AgentResult(
                    success=True,
                    data={"fixes": [], "patches": []},
                    metadata={"message": "No issues to fix"}
                )
            
            # Generate fixes for high and medium priority issues
            fixes = []
            for issue in issues:
                if issue.get('severity') in ['high', 'medium']:
                    fix = await self._generate_fix(issue, context)
                    if fix:
                        fixes.append(fix)
            
            # Create patches
            patches = await self._create_patches(fixes, context)
            
            result_data = {
                "fixes": fixes,
                "patches": patches,
                "summary": {
                    "total_fixes": len(fixes),
                    "successful_fixes": len([f for f in fixes if f.get('success')]),
                    "patches_created": len(patches)
                }
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "issues_processed": len(issues),
                    "fixes_generated": len(fixes)
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"context": "code_fixing"}
            )
    
    async def _generate_fix(self, issue: Dict[str, Any], context: AgentContext) -> Optional[Dict[str, Any]]:
        """Generate a fix for a specific issue."""
        try:
            file_path = issue.get('file', '')
            if not file_path or not os.path.exists(file_path):
                return None
            
            # Read the original file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Create fix prompt
            prompt = f"""
            Generate a fix for this issue:
            
            Issue Type: {issue.get('category', 'unknown')}
            Severity: {issue.get('severity', 'medium')}
            Description: {issue.get('message', '')}
            File: {os.path.basename(file_path)}
            Line: {issue.get('line', 0)}
            
            Original Code:
            ```{self._get_language_from_file(file_path)}
            {original_content}
            ```
            
            Please provide:
            1. The fixed code (complete file or specific section)
            2. Explanation of the fix
            3. Any additional considerations
            
            Respond in JSON format:
            {{
                "fixed_code": "complete fixed code",
                "explanation": "explanation of the fix",
                "considerations": "additional considerations",
                "line_changes": [
                    {{
                        "line": line_number,
                        "original": "original line",
                        "fixed": "fixed line"
                    }}
                ]
            }}
            """
            
            request = LLMRequest(
                prompt=prompt,
                system_message="You are an expert software developer. Generate safe and effective code fixes.",
                temperature=0.1
            )
            
            response = await self.call_llm(request)
            
            if response.content:
                try:
                    fix_data = json.loads(response.content)
                    return {
                        'issue_id': issue.get('id', ''),
                        'file': file_path,
                        'original_content': original_content,
                        'fixed_content': fix_data.get('fixed_code', ''),
                        'explanation': fix_data.get('explanation', ''),
                        'considerations': fix_data.get('considerations', ''),
                        'line_changes': fix_data.get('line_changes', []),
                        'success': True
                    }
                except json.JSONDecodeError:
                    return {
                        'issue_id': issue.get('id', ''),
                        'file': file_path,
                        'original_content': original_content,
                        'fixed_content': response.content,
                        'explanation': 'Fix generated by LLM',
                        'success': False,
                        'error': 'Invalid JSON response'
                    }
            
        except Exception as e:
            return {
                'issue_id': issue.get('id', ''),
                'file': issue.get('file', ''),
                'success': False,
                'error': str(e)
            }
    
    async def _create_patches(self, fixes: List[Dict[str, Any]], context: AgentContext) -> List[Dict[str, Any]]:
        """Create patches from fixes."""
        patches = []
        
        for fix in fixes:
            if not fix.get('success'):
                continue
            
            try:
                patch = await self._create_patch(fix, context)
                if patch:
                    patches.append(patch)
            except Exception as e:
                self.logger.warning(f"Failed to create patch for {fix.get('file', '')}: {e}")
        
        return patches
    
    async def _create_patch(self, fix: Dict[str, Any], context: AgentContext) -> Optional[Dict[str, Any]]:
        """Create a patch for a single fix."""
        try:
            original_content = fix.get('original_content', '')
            fixed_content = fix.get('fixed_content', '')
            
            if not original_content or not fixed_content:
                return None
            
            # Create patch file
            patch_file = os.path.join(
                context.working_directory,
                f"fix_{os.path.basename(fix.get('file', ''))}.patch"
            )
            
            # Generate unified diff
            diff_content = self._generate_unified_diff(
                fix.get('file', ''),
                original_content,
                fixed_content
            )
            
            with open(patch_file, 'w') as f:
                f.write(diff_content)
            
            return {
                'file': fix.get('file', ''),
                'patch_file': patch_file,
                'diff_content': diff_content,
                'explanation': fix.get('explanation', ''),
                'issue_id': fix.get('issue_id', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error creating patch: {e}")
            return None
    
    def _generate_unified_diff(self, file_path: str, original: str, fixed: str) -> str:
        """Generate unified diff format."""
        import difflib
        
        original_lines = original.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f'a/{os.path.basename(file_path)}',
            tofile=f'b/{os.path.basename(file_path)}',
            lineterm=''
        )
        
        return '\n'.join(diff)
    
    def _get_language_from_file(self, file_path: str) -> str:
        """Get programming language from file extension."""
        ext = os.path.splitext(file_path)[1].lower()
        
        lang_map = {
            '.py': 'python',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.hxx': 'cpp',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust'
        }
        
        return lang_map.get(ext, 'text')