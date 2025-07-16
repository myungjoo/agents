"""
Test Runner Agent Implementation

Validates fixes and measures performance improvements for code changes.
"""

import os
import subprocess
import json
import time
import psutil
from typing import Dict, Any, List, Optional

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult


class TestRunner(BaseAgent):
    """Agent for testing fixes and measuring improvements."""
    
    def __init__(self):
        super().__init__(AgentType.TEST_RUNNER, "Test Runner")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "Test Runner",
            "description": "Validates fixes and measures performance improvements",
            "capabilities": [
                "Fix validation",
                "Performance benchmarking",
                "Test execution",
                "Metrics collection"
            ],
            "supported_languages": ["c", "cpp", "python", "java", "javascript", "typescript", "go", "rust"],
            "outputs": [
                "test_results",
                "performance_metrics",
                "validation_status"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute testing and validation."""
        try:
            # Get code fixer results
            code_fixer = context.agent_results.get('code_fixer')
            if not code_fixer or not code_fixer.success:
                return AgentResult(
                    success=True,
                    data={"test_results": [], "performance_metrics": {}},
                    metadata={"message": "No fixes to test"}
                )
            
            fixes = code_fixer.data.get('fixes', [])
            if not fixes:
                return AgentResult(
                    success=True,
                    data={"test_results": [], "performance_metrics": {}},
                    metadata={"message": "No fixes to test"}
                )
            
            # Test each fix
            test_results = []
            for fix in fixes:
                if fix.get('success'):
                    result = await self._test_fix(fix, context)
                    test_results.append(result)
            
            # Collect performance metrics
            performance_metrics = await self._collect_performance_metrics(context)
            
            result_data = {
                "test_results": test_results,
                "performance_metrics": performance_metrics,
                "summary": {
                    "total_tests": len(test_results),
                    "passed_tests": len([r for r in test_results if r.get('status') == 'passed']),
                    "failed_tests": len([r for r in test_results if r.get('status') == 'failed'])
                }
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "fixes_tested": len(fixes),
                    "tests_executed": len(test_results)
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"context": "testing"}
            )
    
    async def _test_fix(self, fix: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Test a single fix."""
        try:
            file_path = fix.get('file', '')
            fixed_content = fix.get('fixed_content', '')
            
            if not file_path or not fixed_content:
                return {
                    'fix_id': fix.get('issue_id', ''),
                    'status': 'skipped',
                    'reason': 'Missing file or content'
                }
            
            # Create backup of original file
            backup_path = f"{file_path}.backup"
            with open(file_path, 'r') as f:
                original_content = f.read()
            
            with open(backup_path, 'w') as f:
                f.write(original_content)
            
            # Apply fix
            with open(file_path, 'w') as f:
                f.write(fixed_content)
            
            # Run tests
            test_result = await self._run_tests(file_path, context)
            
            # Restore original file
            with open(file_path, 'w') as f:
                f.write(original_content)
            
            # Clean up backup
            os.remove(backup_path)
            
            return {
                'fix_id': fix.get('issue_id', ''),
                'file': file_path,
                'status': test_result.get('status', 'unknown'),
                'test_output': test_result.get('output', ''),
                'execution_time': test_result.get('execution_time', 0),
                'memory_usage': test_result.get('memory_usage', 0)
            }
            
        except Exception as e:
            return {
                'fix_id': fix.get('issue_id', ''),
                'status': 'error',
                'error': str(e)
            }
    
    async def _run_tests(self, file_path: str, context: AgentContext) -> Dict[str, Any]:
        """Run tests for a file."""
        try:
            # Determine test command based on file type
            test_command = self._get_test_command(file_path, context)
            
            if not test_command:
                return {
                    'status': 'skipped',
                    'reason': 'No test command available'
                }
            
            # Run test with timeout
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(file_path)
            )
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'output': result.stdout + result.stderr,
                'execution_time': end_time - start_time,
                'memory_usage': end_memory - start_memory,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'reason': 'Test execution timed out'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_test_command(self, file_path: str, context: AgentContext) -> Optional[str]:
        """Get appropriate test command for file type."""
        ext = os.path.splitext(file_path)[1].lower()
        
        # Get build system info from repository analysis
        repo_analysis = context.agent_results.get('repository_analyzer')
        build_system = repo_analysis.data.get('build_system', {}) if repo_analysis else {}
        build_type = build_system.get('type', 'unknown')
        
        # Language-specific test commands
        if ext == '.py':
            return 'python -m pytest -v'
        elif ext in ['.c', '.cpp', '.cc', '.cxx']:
            if build_type == 'make':
                return 'make test'
            elif build_type == 'cmake':
                return 'make test'
            else:
                return None
        elif ext == '.js':
            return 'npm test'
        elif ext == '.java':
            if build_type == 'maven':
                return 'mvn test'
            elif build_type == 'gradle':
                return 'gradle test'
            else:
                return None
        elif ext == '.go':
            return 'go test ./...'
        elif ext == '.rs':
            return 'cargo test'
        
        return None
    
    async def _collect_performance_metrics(self, context: AgentContext) -> Dict[str, Any]:
        """Collect performance metrics for the project."""
        metrics = {
            'build_time': 0,
            'test_time': 0,
            'memory_usage': 0,
            'cpu_usage': 0
        }
        
        try:
            # Get build system info
            repo_analysis = context.agent_results.get('repository_analyzer')
            if not repo_analysis:
                return metrics
            
            build_system = repo_analysis.data.get('build_system', {})
            build_type = build_system.get('type', 'unknown')
            
            # Measure build performance
            build_command = self._get_build_command(build_type)
            if build_command:
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                result = subprocess.run(
                    build_command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss
                
                metrics['build_time'] = end_time - start_time
                metrics['memory_usage'] = end_memory - start_memory
                metrics['build_success'] = result.returncode == 0
            
        except Exception as e:
            self.logger.warning(f"Error collecting performance metrics: {e}")
        
        return metrics
    
    def _get_build_command(self, build_type: str) -> Optional[str]:
        """Get build command for build system type."""
        commands = {
            'make': 'make clean && make',
            'cmake': 'mkdir -p build && cd build && cmake .. && make',
            'maven': 'mvn clean compile',
            'gradle': 'gradle clean build',
            'npm': 'npm install && npm run build',
            'pip': 'pip install -e .',
            'cargo': 'cargo build',
            'go': 'go build ./...'
        }
        
        return commands.get(build_type)