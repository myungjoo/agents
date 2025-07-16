"""
Issue Detector Agent Implementation

Detects correctness bugs, memory bugs, and performance issues
in source code using static analysis and LLM-based analysis.
"""

import os
import subprocess
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import ast
import tempfile

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from common.llm import LLMRequest


class IssueDetector(BaseAgent):
    """Agent for detecting issues in source code."""
    
    def __init__(self):
        super().__init__(AgentType.ISSUE_DETECTOR, "Issue Detector")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "Issue Detector",
            "description": "Detects correctness bugs, memory bugs, and performance issues",
            "capabilities": [
                "Static code analysis",
                "LLM-based code review",
                "Memory leak detection",
                "Performance bottleneck identification",
                "Security vulnerability detection",
                "Code quality assessment"
            ],
            "supported_languages": ["c", "cpp", "python", "java", "javascript", "typescript", "go", "rust"],
            "outputs": [
                "issues",
                "issue_categories",
                "severity_levels",
                "affected_files",
                "recommendations"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute issue detection."""
        try:
            # Get repository analysis results
            repo_analysis = context.agent_results.get('repository_analyzer')
            if not repo_analysis or not repo_analysis.success:
                raise Exception("Repository analysis not available")
            
            repo_path = repo_analysis.data.get('repository_path')
            if not repo_path or not os.path.exists(repo_path):
                raise Exception("Repository path not found")
            
            # Get repository information
            languages = repo_analysis.data.get('languages', {})
            primary_lang = languages.get('primary', 'unknown')
            
            # Detect issues using multiple methods
            issues = []
            
            # Static analysis
            static_issues = await self._static_analysis(repo_path, primary_lang)
            issues.extend(static_issues)
            
            # LLM-based analysis
            llm_issues = await self._llm_analysis(repo_path, primary_lang, languages)
            issues.extend(llm_issues)
            
            # Performance analysis
            perf_issues = await self._performance_analysis(repo_path, primary_lang)
            issues.extend(perf_issues)
            
            # Security analysis
            security_issues = await self._security_analysis(repo_path, primary_lang)
            issues.extend(security_issues)
            
            # Categorize and prioritize issues
            categorized_issues = await self._categorize_issues(issues)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(categorized_issues)
            
            result_data = {
                "issues": issues,
                "categorized_issues": categorized_issues,
                "recommendations": recommendations,
                "summary": {
                    "total_issues": len(issues),
                    "high_impact": len([i for i in issues if i.get('severity') == 'high']),
                    "medium_impact": len([i for i in issues if i.get('severity') == 'medium']),
                    "low_impact": len([i for i in issues if i.get('severity') == 'low']),
                    "affected_files": len(set(i.get('file') for i in issues if i.get('file')))
                }
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "repository_path": repo_path,
                    "primary_language": primary_lang,
                    "analysis_methods": ["static", "llm", "performance", "security"]
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={
                    "repository_path": context.working_directory
                }
            )
    
    async def _static_analysis(self, repo_path: str, primary_lang: str) -> List[Dict[str, Any]]:
        """Perform static analysis on the codebase."""
        issues = []
        
        try:
            if primary_lang == "python":
                issues.extend(await self._analyze_python_static(repo_path))
            elif primary_lang in ["c", "cpp"]:
                issues.extend(await self._analyze_cpp_static(repo_path))
            elif primary_lang == "javascript":
                issues.extend(await self._analyze_javascript_static(repo_path))
            elif primary_lang == "java":
                issues.extend(await self._analyze_java_static(repo_path))
            elif primary_lang == "go":
                issues.extend(await self._analyze_go_static(repo_path))
            elif primary_lang == "rust":
                issues.extend(await self._analyze_rust_static(repo_path))
            
        except Exception as e:
            self.logger.warning(f"Static analysis failed: {e}")
        
        return issues
    
    async def _analyze_python_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for Python code."""
        issues = []
        
        # Use pylint for static analysis
        try:
            result = subprocess.run(
                ['pylint', '--output-format=json', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                pylint_issues = json.loads(result.stdout)
                for issue in pylint_issues:
                    issues.append({
                        'type': 'static_analysis',
                        'category': 'code_quality',
                        'severity': self._map_pylint_severity(issue.get('type', 'convention')),
                        'message': issue.get('message', ''),
                        'file': issue.get('path', ''),
                        'line': issue.get('line', 0),
                        'column': issue.get('column', 0),
                        'symbol': issue.get('symbol', ''),
                        'tool': 'pylint'
                    })
        
        except Exception as e:
            self.logger.warning(f"Pylint analysis failed: {e}")
        
        # Use flake8 for additional checks
        try:
            result = subprocess.run(
                ['flake8', '--format=json', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                flake8_issues = json.loads(result.stdout)
                for file_path, file_issues in flake8_issues.items():
                    for issue in file_issues:
                        issues.append({
                            'type': 'static_analysis',
                            'category': 'code_style',
                            'severity': 'low',
                            'message': issue.get('text', ''),
                            'file': file_path,
                            'line': issue.get('line_number', 0),
                            'column': issue.get('column_number', 0),
                            'code': issue.get('code', ''),
                            'tool': 'flake8'
                        })
        
        except Exception as e:
            self.logger.warning(f"Flake8 analysis failed: {e}")
        
        return issues
    
    async def _analyze_cpp_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for C/C++ code."""
        issues = []
        
        # Use cppcheck for static analysis
        try:
            result = subprocess.run(
                ['cppcheck', '--enable=all', '--xml', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse XML output (simplified)
            if result.stdout:
                # Basic XML parsing for cppcheck output
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(result.stdout)
                    for error in root.findall('.//error'):
                        issues.append({
                            'type': 'static_analysis',
                            'category': 'memory_safety',
                            'severity': 'medium',
                            'message': error.get('msg', ''),
                            'file': error.get('file', ''),
                            'line': int(error.get('line', 0)),
                            'tool': 'cppcheck'
                        })
                except ET.ParseError:
                    pass
        
        except Exception as e:
            self.logger.warning(f"Cppcheck analysis failed: {e}")
        
        return issues
    
    async def _analyze_javascript_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for JavaScript code."""
        issues = []
        
        # Use ESLint if available
        try:
            result = subprocess.run(
                ['npx', 'eslint', '--format=json', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                eslint_issues = json.loads(result.stdout)
                for file_issues in eslint_issues:
                    for issue in file_issues.get('messages', []):
                        issues.append({
                            'type': 'static_analysis',
                            'category': 'code_quality',
                            'severity': self._map_eslint_severity(issue.get('severity', 1)),
                            'message': issue.get('message', ''),
                            'file': file_issues.get('filePath', ''),
                            'line': issue.get('line', 0),
                            'column': issue.get('column', 0),
                            'rule': issue.get('ruleId', ''),
                            'tool': 'eslint'
                        })
        
        except Exception as e:
            self.logger.warning(f"ESLint analysis failed: {e}")
        
        return issues
    
    async def _analyze_java_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for Java code."""
        issues = []
        
        # Use SpotBugs if available
        try:
            result = subprocess.run(
                ['spotbugs', '-xml', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                # Basic XML parsing for SpotBugs output
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(result.stdout)
                    for bug in root.findall('.//BugInstance'):
                        issues.append({
                            'type': 'static_analysis',
                            'category': 'bug_pattern',
                            'severity': 'medium',
                            'message': bug.get('type', ''),
                            'file': bug.get('sourcepath', ''),
                            'line': int(bug.get('line', 0)),
                            'tool': 'spotbugs'
                        })
                except ET.ParseError:
                    pass
        
        except Exception as e:
            self.logger.warning(f"SpotBugs analysis failed: {e}")
        
        return issues
    
    async def _analyze_go_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for Go code."""
        issues = []
        
        # Use golint
        try:
            result = subprocess.run(
                ['golint', repo_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            file_path = parts[0]
                            line_num = int(parts[1])
                            message = ':'.join(parts[2:]).strip()
                            
                            issues.append({
                                'type': 'static_analysis',
                                'category': 'code_style',
                                'severity': 'low',
                                'message': message,
                                'file': file_path,
                                'line': line_num,
                                'tool': 'golint'
                            })
        
        except Exception as e:
            self.logger.warning(f"Golint analysis failed: {e}")
        
        return issues
    
    async def _analyze_rust_static(self, repo_path: str) -> List[Dict[str, Any]]:
        """Static analysis for Rust code."""
        issues = []
        
        # Use cargo clippy
        try:
            result = subprocess.run(
                ['cargo', 'clippy', '--message-format=json'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        try:
                            clippy_issue = json.loads(line)
                            if 'message' in clippy_issue:
                                message = clippy_issue['message']
                                issues.append({
                                    'type': 'static_analysis',
                                    'category': 'code_quality',
                                    'severity': 'medium',
                                    'message': message.get('message', ''),
                                    'file': message.get('spans', [{}])[0].get('file_name', ''),
                                    'line': message.get('spans', [{}])[0].get('line_start', 0),
                                    'tool': 'clippy'
                                })
                        except json.JSONDecodeError:
                            continue
        
        except Exception as e:
            self.logger.warning(f"Cargo clippy analysis failed: {e}")
        
        return issues
    
    async def _llm_analysis(self, repo_path: str, primary_lang: str, languages: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform LLM-based code analysis."""
        issues = []
        
        # Analyze key source files
        source_files = await self._get_source_files(repo_path, primary_lang)
        
        for file_path in source_files[:10]:  # Limit to first 10 files for performance
            try:
                file_issues = await self._analyze_file_with_llm(file_path, primary_lang)
                issues.extend(file_issues)
            except Exception as e:
                self.logger.warning(f"LLM analysis failed for {file_path}: {e}")
        
        return issues
    
    async def _get_source_files(self, repo_path: str, primary_lang: str) -> List[str]:
        """Get list of source files to analyze."""
        source_files = []
        
        # File extensions by language
        extensions = {
            "python": [".py"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            "javascript": [".js", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "go": [".go"],
            "rust": [".rs"]
        }
        
        lang_extensions = extensions.get(primary_lang, [])
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in lang_extensions):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
        
        return source_files
    
    async def _analyze_file_with_llm(self, file_path: str, primary_lang: str) -> List[Dict[str, Any]]:
        """Analyze a single file with LLM."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if len(content) > 10000:  # Skip very large files
                return issues
            
            # Create analysis prompt
            prompt = f"""
            Analyze this {primary_lang} code file for potential issues:
            
            File: {os.path.basename(file_path)}
            
            Code:
            ```{primary_lang}
            {content}
            ```
            
            Look for:
            1. Correctness bugs (logic errors, incorrect algorithms)
            2. Memory issues (leaks, buffer overflows, use-after-free)
            3. Performance problems (inefficient algorithms, unnecessary computations)
            4. Security vulnerabilities (input validation, injection attacks)
            5. Code quality issues (maintainability, readability)
            
            For each issue found, provide:
            - Issue type (correctness/memory/performance/security/quality)
            - Severity (high/medium/low)
            - Description of the problem
            - Line number (if applicable)
            - Suggested fix
            
            Respond in JSON format:
            {{
                "issues": [
                    {{
                        "type": "issue_type",
                        "severity": "severity_level",
                        "description": "description",
                        "line": line_number,
                        "suggestion": "fix_suggestion"
                    }}
                ]
            }}
            """
            
            request = LLMRequest(
                prompt=prompt,
                system_message="You are an expert code reviewer and security analyst. Identify real issues and provide actionable suggestions.",
                temperature=0.1
            )
            
            response = await self.call_llm(request)
            
            if response.content:
                try:
                    result = json.loads(response.content)
                    for issue in result.get('issues', []):
                        issues.append({
                            'type': 'llm_analysis',
                            'category': issue.get('type', 'unknown'),
                            'severity': issue.get('severity', 'medium'),
                            'message': issue.get('description', ''),
                            'file': file_path,
                            'line': issue.get('line', 0),
                            'suggestion': issue.get('suggestion', ''),
                            'tool': 'llm'
                        })
                except json.JSONDecodeError:
                    # Fallback: extract issues from text
                    issues.extend(self._extract_issues_from_text(response.content, file_path))
            
        except Exception as e:
            self.logger.warning(f"Error analyzing file {file_path}: {e}")
        
        return issues
    
    def _extract_issues_from_text(self, text: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract issues from LLM text response."""
        issues = []
        
        # Simple pattern matching for issue extraction
        lines = text.split('\n')
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            
            if 'issue' in line.lower() or 'problem' in line.lower() or 'bug' in line.lower():
                if current_issue:
                    issues.append(current_issue)
                current_issue = {
                    'type': 'llm_analysis',
                    'category': 'unknown',
                    'severity': 'medium',
                    'message': line,
                    'file': file_path,
                    'line': 0,
                    'tool': 'llm'
                }
        
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    async def _performance_analysis(self, repo_path: str, primary_lang: str) -> List[Dict[str, Any]]:
        """Analyze code for performance issues."""
        issues = []
        
        # Language-specific performance analysis
        if primary_lang == "python":
            issues.extend(await self._analyze_python_performance(repo_path))
        elif primary_lang in ["c", "cpp"]:
            issues.extend(await self._analyze_cpp_performance(repo_path))
        elif primary_lang == "javascript":
            issues.extend(await self._analyze_javascript_performance(repo_path))
        
        return issues
    
    async def _analyze_python_performance(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze Python code for performance issues."""
        issues = []
        
        # Common performance anti-patterns
        anti_patterns = [
            (r'for\s+\w+\s+in\s+range\(len\(', 'Consider using enumerate() instead of range(len())'),
            (r'\.append\(.*\)\s+in\s+loop', 'Consider using list comprehension for better performance'),
            (r'import\s+\*', 'Avoid wildcard imports for better performance and clarity'),
            (r'\.keys\(\)\s*\[\s*\]', 'Use .get() instead of .keys()[] for safer access'),
        ]
        
        for pattern, message in anti_patterns:
            issues.extend(await self._find_pattern_in_files(repo_path, pattern, message, 'performance'))
        
        return issues
    
    async def _analyze_cpp_performance(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze C++ code for performance issues."""
        issues = []
        
        # Common C++ performance anti-patterns
        anti_patterns = [
            (r'std::endl', 'Use \\n instead of std::endl for better performance'),
            (r'new\s+\w+\s*\[\s*\]', 'Consider using std::vector instead of raw arrays'),
            (r'std::string\s+\w+\s*\+\s*std::string', 'Consider using std::stringstream for multiple concatenations'),
        ]
        
        for pattern, message in anti_patterns:
            issues.extend(await self._find_pattern_in_files(repo_path, pattern, message, 'performance'))
        
        return issues
    
    async def _analyze_javascript_performance(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript code for performance issues."""
        issues = []
        
        # Common JavaScript performance anti-patterns
        anti_patterns = [
            (r'for\s*\(\s*var\s+\w+\s*=\s*0', 'Consider using let instead of var in for loops'),
            (r'\.innerHTML\s*=', 'Consider using textContent for better performance'),
            (r'\.getElementById\s*\(\s*[\'"]\w+[\'"]\s*\)\s*\.', 'Cache DOM elements for better performance'),
        ]
        
        for pattern, message in anti_patterns:
            issues.extend(await self._find_pattern_in_files(repo_path, pattern, message, 'performance'))
        
        return issues
    
    async def _find_pattern_in_files(self, repo_path: str, pattern: str, message: str, category: str) -> List[Dict[str, Any]]:
        """Find pattern in source files."""
        issues = []
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.py', '.cpp', '.c', '.js', '.ts', '.java', '.go', '.rs')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        for line_num, line in enumerate(content.split('\n'), 1):
                            if re.search(pattern, line):
                                issues.append({
                                    'type': 'pattern_analysis',
                                    'category': category,
                                    'severity': 'medium',
                                    'message': message,
                                    'file': file_path,
                                    'line': line_num,
                                    'tool': 'regex_pattern'
                                })
                    except Exception:
                        continue
        
        return issues
    
    async def _security_analysis(self, repo_path: str, primary_lang: str) -> List[Dict[str, Any]]:
        """Analyze code for security vulnerabilities."""
        issues = []
        
        # Common security patterns
        security_patterns = [
            (r'exec\s*\(', 'Potential code injection vulnerability'),
            (r'eval\s*\(', 'Potential code injection vulnerability'),
            (r'\.format\s*\(.*\{.*\}', 'Potential format string vulnerability'),
            (r'strcpy\s*\(', 'Potential buffer overflow vulnerability'),
            (r'gets\s*\(', 'Buffer overflow vulnerability - use fgets instead'),
            (r'sql\s*\+\s*', 'Potential SQL injection - use parameterized queries'),
            (r'innerHTML\s*=\s*.*\+', 'Potential XSS vulnerability'),
        ]
        
        for pattern, message in security_patterns:
            issues.extend(await self._find_pattern_in_files(repo_path, pattern, message, 'security'))
        
        return issues
    
    async def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize and prioritize issues."""
        categorized = {
            'correctness': [],
            'memory': [],
            'performance': [],
            'security': [],
            'quality': [],
            'by_severity': {
                'high': [],
                'medium': [],
                'low': []
            }
        }
        
        for issue in issues:
            category = issue.get('category', 'quality')
            severity = issue.get('severity', 'medium')
            
            if category in categorized:
                categorized[category].append(issue)
            
            if severity in categorized['by_severity']:
                categorized['by_severity'][severity].append(issue)
        
        return categorized
    
    async def _generate_recommendations(self, categorized_issues: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on detected issues."""
        recommendations = []
        
        # High priority recommendations
        high_issues = categorized_issues['by_severity']['high']
        if high_issues:
            recommendations.append({
                'priority': 'high',
                'title': 'Address High Severity Issues',
                'description': f'Found {len(high_issues)} high severity issues that should be addressed immediately.',
                'issues': high_issues[:5]  # Top 5 issues
            })
        
        # Security recommendations
        security_issues = categorized_issues['security']
        if security_issues:
            recommendations.append({
                'priority': 'high',
                'title': 'Security Vulnerabilities Detected',
                'description': f'Found {len(security_issues)} potential security vulnerabilities.',
                'issues': security_issues[:3]
            })
        
        # Performance recommendations
        performance_issues = categorized_issues['performance']
        if performance_issues:
            recommendations.append({
                'priority': 'medium',
                'title': 'Performance Issues Found',
                'description': f'Found {len(performance_issues)} performance-related issues.',
                'issues': performance_issues[:3]
            })
        
        # Code quality recommendations
        quality_issues = categorized_issues['quality']
        if quality_issues:
            recommendations.append({
                'priority': 'low',
                'title': 'Code Quality Improvements',
                'description': f'Found {len(quality_issues)} code quality issues.',
                'issues': quality_issues[:3]
            })
        
        return recommendations
    
    def _map_pylint_severity(self, pylint_type: str) -> str:
        """Map pylint severity to our severity levels."""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'convention': 'low',
            'refactor': 'low'
        }
        return mapping.get(pylint_type, 'medium')
    
    def _map_eslint_severity(self, eslint_severity: int) -> str:
        """Map ESLint severity to our severity levels."""
        mapping = {
            0: 'low',
            1: 'medium',
            2: 'high'
        }
        return mapping.get(eslint_severity, 'medium')