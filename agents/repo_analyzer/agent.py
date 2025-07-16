#!/usr/bin/env python3
"""
Repository Analyzer Agent
Analyzes GitHub repositories for structure, purpose, build instructions, and test procedures
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import git
import tree_sitter
from tree_sitter import Language, Parser

from ..base_agent import BaseAgent, TaskResult
from common.utils.logging import get_agent_logger


class RepoAnalyzerAgent(BaseAgent):
    """Agent for analyzing repository structure and purpose"""
    
    def __init__(self, agent_id: str, config, llm_manager):
        """Initialize repository analyzer agent"""
        super().__init__(agent_id, config, llm_manager)
        
        self.max_repo_size = self._parse_size(
            config.get("agents.repo_analyzer.max_repo_size", "500MB")
        )
        self.supported_languages = config.get(
            "agents.repo_analyzer.supported_languages",
            ["python", "c", "cpp", "javascript", "java", "go", "rust"]
        )
        
        # Setup tree-sitter parsers
        self.parsers = {}
        self._setup_parsers()
    
    def _setup_parsers(self) -> None:
        """Setup tree-sitter parsers for code analysis"""
        try:
            # Note: In a real implementation, you'd need to build the tree-sitter languages
            # For now, we'll use a simple approach
            self.logger.info("Tree-sitter parsers initialized")
        except Exception as e:
            self.logger.warning(f"Failed to setup tree-sitter parsers: {e}")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        elif size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        else:
            return int(size_str)
    
    def get_capabilities(self) -> List[str]:
        """Get agent capabilities"""
        return [
            "repository_cloning",
            "structure_analysis", 
            "language_detection",
            "build_system_analysis",
            "test_discovery",
            "documentation_analysis",
            "dependency_analysis"
        ]
    
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """
        Process repository analysis task
        
        Args:
            task: Task containing repository URL and analysis options
            
        Returns:
            TaskResult with analysis results
        """
        task_type = task.get("type")
        
        if task_type == "analyze_repository":
            return await self._analyze_repository(task)
        else:
            return TaskResult(
                success=False,
                error=f"Unknown task type: {task_type}"
            )
    
    async def _analyze_repository(self, task: Dict[str, Any]) -> TaskResult:
        """Analyze a GitHub repository"""
        repo_url = task.get("repository_url")
        if not repo_url:
            return TaskResult(success=False, error="No repository URL provided")
        
        temp_dir = None
        try:
            # Clone repository
            self.logger.info(f"Cloning repository: {repo_url}")
            temp_dir = tempfile.mkdtemp()
            repo_path = Path(temp_dir) / "repo"
            
            # Clone with depth=1 for faster cloning
            repo = git.Repo.clone_from(repo_url, repo_path, depth=1)
            
            # Check repository size
            repo_size = self._get_directory_size(repo_path)
            if repo_size > self.max_repo_size:
                return TaskResult(
                    success=False,
                    error=f"Repository too large: {repo_size} bytes (max: {self.max_repo_size})"
                )
            
            # Perform analysis
            analysis_results = {
                "repository_url": repo_url,
                "clone_info": {
                    "size_bytes": repo_size,
                    "commit_hash": repo.head.commit.hexsha,
                    "last_commit_date": repo.head.commit.committed_datetime.isoformat()
                },
                "structure": await self._analyze_structure(repo_path),
                "languages": await self._detect_languages(repo_path),
                "build_system": await self._analyze_build_system(repo_path),
                "tests": await self._discover_tests(repo_path),
                "documentation": await self._analyze_documentation(repo_path),
                "dependencies": await self._analyze_dependencies(repo_path),
                "purpose": await self._infer_purpose(repo_path),
                "usage_examples": await self._find_usage_examples(repo_path)
            }
            
            return TaskResult(
                success=True,
                data=analysis_results,
                metrics={
                    "repo_size_bytes": repo_size,
                    "files_analyzed": analysis_results["structure"]["total_files"],
                    "languages_detected": len(analysis_results["languages"])
                }
            )
            
        except Exception as e:
            self.logger.error(f"Repository analysis failed: {e}")
            return TaskResult(success=False, error=str(e))
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
    
    async def _analyze_structure(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze repository structure"""
        structure = {
            "total_files": 0,
            "total_directories": 0,
            "file_types": {},
            "directory_structure": {},
            "important_files": []
        }
        
        important_files = [
            "README.md", "README.rst", "README.txt",
            "Makefile", "CMakeLists.txt", "build.gradle", "pom.xml",
            "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
            "Cargo.toml", "go.mod", "Dockerfile", ".gitignore",
            "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md"
        ]
        
        for item in repo_path.rglob('*'):
            if item.is_file():
                structure["total_files"] += 1
                ext = item.suffix.lower()
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                if item.name in important_files:
                    structure["important_files"].append(str(item.relative_to(repo_path)))
            elif item.is_dir():
                structure["total_directories"] += 1
        
        return structure
    
    async def _detect_languages(self, repo_path: Path) -> Dict[str, Any]:
        """Detect programming languages in repository"""
        languages = {}
        
        language_extensions = {
            "python": [".py", ".pyx", ".pyi"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cxx", ".cc", ".hpp", ".hxx"],
            "java": [".java"],
            "go": [".go"],
            "rust": [".rs"],
            "shell": [".sh", ".bash", ".zsh"],
            "yaml": [".yml", ".yaml"],
            "json": [".json"],
            "markdown": [".md", ".markdown"]
        }
        
        for item in repo_path.rglob('*'):
            if item.is_file():
                ext = item.suffix.lower()
                for lang, exts in language_extensions.items():
                    if ext in exts:
                        if lang not in languages:
                            languages[lang] = {"files": 0, "lines": 0}
                        languages[lang]["files"] += 1
                        
                        try:
                            with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = len(f.readlines())
                                languages[lang]["lines"] += lines
                        except:
                            pass
        
        return languages
    
    async def _analyze_build_system(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze build system and dependencies"""
        build_systems = {}
        
        # Check for common build files
        build_files = {
            "Makefile": "make",
            "CMakeLists.txt": "cmake",
            "build.gradle": "gradle",
            "pom.xml": "maven",
            "package.json": "npm",
            "requirements.txt": "pip",
            "Pipfile": "pipenv",
            "pyproject.toml": "poetry",
            "Cargo.toml": "cargo",
            "go.mod": "go",
            "Dockerfile": "docker"
        }
        
        for filename, build_system in build_files.items():
            build_file = repo_path / filename
            if build_file.exists():
                build_systems[build_system] = {
                    "file": filename,
                    "exists": True
                }
                
                # Extract basic information
                try:
                    content = build_file.read_text(encoding='utf-8', errors='ignore')
                    build_systems[build_system]["content_snippet"] = content[:500]
                except:
                    pass
        
        return build_systems
    
    async def _discover_tests(self, repo_path: Path) -> Dict[str, Any]:
        """Discover test files and frameworks"""
        tests = {
            "test_directories": [],
            "test_files": [],
            "frameworks": []
        }
        
        # Common test directory patterns
        test_dirs = ["test", "tests", "__tests__", "spec", "specs"]
        
        for item in repo_path.rglob('*'):
            if item.is_dir() and any(pattern in item.name.lower() for pattern in test_dirs):
                tests["test_directories"].append(str(item.relative_to(repo_path)))
            elif item.is_file():
                name_lower = item.name.lower()
                if any(pattern in name_lower for pattern in ["test_", "test.", "_test", ".test"]):
                    tests["test_files"].append(str(item.relative_to(repo_path)))
        
        # Check for test frameworks
        framework_indicators = {
            "pytest": ["pytest", "conftest.py"],
            "unittest": ["unittest"],
            "jest": ["jest"],
            "mocha": ["mocha"],
            "junit": ["junit"],
            "googletest": ["gtest"]
        }
        
        for framework, indicators in framework_indicators.items():
            for indicator in indicators:
                if any(indicator in str(f).lower() for f in repo_path.rglob('*')):
                    tests["frameworks"].append(framework)
                    break
        
        return tests
    
    async def _analyze_documentation(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze documentation structure"""
        docs = {
            "readme_files": [],
            "doc_directories": [],
            "documentation_files": []
        }
        
        readme_patterns = ["readme", "read_me"]
        doc_dirs = ["doc", "docs", "documentation"]
        doc_extensions = [".md", ".rst", ".txt", ".html"]
        
        for item in repo_path.rglob('*'):
            if item.is_file():
                name_lower = item.name.lower()
                if any(pattern in name_lower for pattern in readme_patterns):
                    docs["readme_files"].append(str(item.relative_to(repo_path)))
                elif item.suffix.lower() in doc_extensions:
                    docs["documentation_files"].append(str(item.relative_to(repo_path)))
            elif item.is_dir():
                if any(pattern in item.name.lower() for pattern in doc_dirs):
                    docs["doc_directories"].append(str(item.relative_to(repo_path)))
        
        return docs
    
    async def _analyze_dependencies(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {}
        
        # Python dependencies
        req_file = repo_path / "requirements.txt"
        if req_file.exists():
            try:
                content = req_file.read_text()
                deps = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                dependencies["python"] = deps
            except:
                pass
        
        # Node.js dependencies
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                import json
                content = json.loads(package_json.read_text())
                dependencies["node"] = {
                    "dependencies": content.get("dependencies", {}),
                    "devDependencies": content.get("devDependencies", {})
                }
            except:
                pass
        
        return dependencies
    
    async def _infer_purpose(self, repo_path: Path) -> Dict[str, Any]:
        """Infer repository purpose using LLM"""
        try:
            # Read README content
            readme_content = ""
            for readme_file in ["README.md", "README.rst", "README.txt"]:
                readme_path = repo_path / readme_file
                if readme_path.exists():
                    readme_content = readme_path.read_text(encoding='utf-8', errors='ignore')[:2000]
                    break
            
            if not readme_content:
                return {"purpose": "Unknown", "confidence": "low"}
            
            # Use LLM to analyze purpose
            prompt = f"""
            Analyze this README content and infer the purpose of the software project:
            
            {readme_content}
            
            Provide:
            1. A brief description of what this software does
            2. The primary use case or domain
            3. Key features mentioned
            4. Target audience
            """
            
            response = await self.llm_manager.generate_structured(
                prompt,
                {
                    "type": "object",
                    "properties": {
                        "purpose": {"type": "string"},
                        "domain": {"type": "string"},
                        "features": {"type": "array", "items": {"type": "string"}},
                        "target_audience": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                    },
                    "required": ["purpose", "confidence"]
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.warning(f"Failed to infer purpose: {e}")
            return {"purpose": "Unknown", "confidence": "low", "error": str(e)}
    
    async def _find_usage_examples(self, repo_path: Path) -> List[str]:
        """Find usage examples in the repository"""
        examples = []
        
        # Look for example directories
        example_dirs = ["examples", "example", "samples", "demo", "demos"]
        
        for item in repo_path.rglob('*'):
            if item.is_dir() and any(pattern in item.name.lower() for pattern in example_dirs):
                examples.append(str(item.relative_to(repo_path)))
        
        return examples