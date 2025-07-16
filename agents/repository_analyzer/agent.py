"""
Repository Analyzer Agent Implementation

Analyzes the structure and purpose of a software repository,
identifies build systems, dependencies, and key components.
"""

import os
import subprocess
import json
import yaml
import toml
from typing import Dict, Any, List, Optional
from pathlib import Path
import git

from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
from common.llm import LLMRequest


class RepositoryAnalyzer(BaseAgent):
    """Agent for analyzing repository structure and purpose."""
    
    def __init__(self):
        super().__init__(AgentType.REPOSITORY_ANALYZER, "Repository Analyzer")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return {
            "name": "Repository Analyzer",
            "description": "Analyzes repository structure, build systems, and dependencies",
            "capabilities": [
                "Repository cloning and structure analysis",
                "Build system identification",
                "Dependency analysis",
                "Language and framework detection",
                "Project purpose inference",
                "Build and test instruction extraction"
            ],
            "supported_languages": ["c", "cpp", "python", "java", "javascript", "typescript", "go", "rust"],
            "outputs": [
                "repository_structure",
                "build_system",
                "dependencies",
                "languages",
                "purpose",
                "build_instructions",
                "test_instructions"
            ]
        }
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute repository analysis."""
        try:
            # Clone repository
            repo_path = await self._clone_repository(context)
            
            # Analyze repository structure
            structure = await self._analyze_structure(repo_path)
            
            # Identify build system
            build_system = await self._identify_build_system(repo_path)
            
            # Analyze dependencies
            dependencies = await self._analyze_dependencies(repo_path, build_system)
            
            # Detect languages and frameworks
            languages = await self._detect_languages(repo_path)
            
            # Infer project purpose
            purpose = await self._infer_purpose(repo_path, structure, languages)
            
            # Extract build and test instructions
            build_instructions = await self._extract_build_instructions(repo_path, build_system)
            test_instructions = await self._extract_test_instructions(repo_path, build_system)
            
            # Compile results
            result_data = {
                "repository_structure": structure,
                "build_system": build_system,
                "dependencies": dependencies,
                "languages": languages,
                "purpose": purpose,
                "build_instructions": build_instructions,
                "test_instructions": test_instructions,
                "repository_path": repo_path
            }
            
            return AgentResult(
                success=True,
                data=result_data,
                metadata={
                    "repository_url": context.repository_url,
                    "branch": context.branch,
                    "analysis_time": self.result.execution_time if self.result else 0
                }
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={
                    "repository_url": context.repository_url,
                    "branch": context.branch
                }
            )
    
    async def _clone_repository(self, context: AgentContext) -> str:
        """Clone the repository to local storage."""
        repo_name = context.repository_url.split('/')[-1].replace('.git', '')
        repo_path = os.path.join(context.working_directory, repo_name)
        
        if os.path.exists(repo_path):
            self.logger.info(f"Repository already exists at {repo_path}")
            return repo_path
        
        self.logger.info(f"Cloning repository {context.repository_url} to {repo_path}")
        
        try:
            git.Repo.clone_from(
                context.repository_url,
                repo_path,
                branch=context.branch,
                depth=1  # Shallow clone for faster download
            )
            self.logger.info(f"Repository cloned successfully")
            return repo_path
        except Exception as e:
            raise Exception(f"Failed to clone repository: {e}")
    
    async def _analyze_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze repository structure."""
        structure = {
            "files": [],
            "directories": [],
            "file_types": {},
            "total_files": 0,
            "total_size": 0
        }
        
        try:
            for root, dirs, files in os.walk(repo_path):
                # Skip hidden directories and common build artifacts
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'build', 'dist']]
                
                for file in files:
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Get file info
                    try:
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        structure["files"].append({
                            "path": rel_path,
                            "size": file_size,
                            "extension": file_ext
                        })
                        
                        structure["total_files"] += 1
                        structure["total_size"] += file_size
                        
                        if file_ext:
                            structure["file_types"][file_ext] = structure["file_types"].get(file_ext, 0) + 1
                            
                    except OSError:
                        continue
            
            # Get directory structure
            for root, dirs, _ in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    rel_path = os.path.relpath(dir_path, repo_path)
                    structure["directories"].append(rel_path)
            
            return structure
            
        except Exception as e:
            self.logger.error(f"Error analyzing structure: {e}")
            return structure
    
    async def _identify_build_system(self, repo_path: str) -> Dict[str, Any]:
        """Identify the build system used in the repository."""
        build_system = {
            "type": "unknown",
            "files": [],
            "config": {},
            "commands": []
        }
        
        # Common build system files
        build_files = {
            "make": ["Makefile", "makefile", "GNUmakefile"],
            "cmake": ["CMakeLists.txt", "cmake/"],
            "autotools": ["configure.ac", "Makefile.am", "autogen.sh"],
            "maven": ["pom.xml"],
            "gradle": ["build.gradle", "gradle/"],
            "npm": ["package.json"],
            "yarn": ["yarn.lock"],
            "pip": ["requirements.txt", "setup.py", "pyproject.toml"],
            "cargo": ["Cargo.toml"],
            "go": ["go.mod", "go.sum"],
            "meson": ["meson.build"],
            "ninja": ["build.ninja"],
            "bazel": ["BUILD", "WORKSPACE"],
            "conan": ["conanfile.txt", "conanfile.py"]
        }
        
        for build_type, files in build_files.items():
            for file_pattern in files:
                if os.path.exists(os.path.join(repo_path, file_pattern)):
                    build_system["type"] = build_type
                    build_system["files"].append(file_pattern)
        
        # Extract build configuration
        if build_system["type"] != "unknown":
            build_system["config"] = await self._extract_build_config(repo_path, build_system["type"])
            build_system["commands"] = await self._get_build_commands(build_system["type"])
        
        return build_system
    
    async def _extract_build_config(self, repo_path: str, build_type: str) -> Dict[str, Any]:
        """Extract configuration from build system files."""
        config = {}
        
        try:
            if build_type == "npm":
                package_json = os.path.join(repo_path, "package.json")
                if os.path.exists(package_json):
                    with open(package_json, 'r') as f:
                        config = json.load(f)
            
            elif build_type == "pip":
                requirements_txt = os.path.join(repo_path, "requirements.txt")
                if os.path.exists(requirements_txt):
                    with open(requirements_txt, 'r') as f:
                        config["requirements"] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                setup_py = os.path.join(repo_path, "setup.py")
                if os.path.exists(setup_py):
                    config["has_setup_py"] = True
            
            elif build_type == "cargo":
                cargo_toml = os.path.join(repo_path, "Cargo.toml")
                if os.path.exists(cargo_toml):
                    with open(cargo_toml, 'r') as f:
                        config = toml.load(f)
            
            elif build_type == "maven":
                pom_xml = os.path.join(repo_path, "pom.xml")
                if os.path.exists(pom_xml):
                    # Basic XML parsing for Maven POM
                    config["has_pom_xml"] = True
            
        except Exception as e:
            self.logger.warning(f"Error extracting build config: {e}")
        
        return config
    
    async def _get_build_commands(self, build_type: str) -> List[str]:
        """Get common build commands for the build system."""
        commands_map = {
            "make": ["make", "make clean", "make install"],
            "cmake": ["cmake ..", "make", "make install"],
            "maven": ["mvn compile", "mvn package", "mvn install"],
            "gradle": ["gradle build", "gradle test", "gradle install"],
            "npm": ["npm install", "npm run build", "npm test"],
            "pip": ["pip install -r requirements.txt", "python setup.py install"],
            "cargo": ["cargo build", "cargo test", "cargo install"],
            "go": ["go build", "go test", "go install"],
            "meson": ["meson setup builddir", "ninja -C builddir"],
            "bazel": ["bazel build //...", "bazel test //..."]
        }
        
        return commands_map.get(build_type, [])
    
    async def _analyze_dependencies(self, repo_path: str, build_system: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project dependencies."""
        dependencies = {
            "direct": [],
            "indirect": [],
            "dev_dependencies": [],
            "build_dependencies": []
        }
        
        build_type = build_system.get("type", "unknown")
        config = build_system.get("config", {})
        
        if build_type == "npm":
            if "dependencies" in config:
                dependencies["direct"] = list(config["dependencies"].keys())
            if "devDependencies" in config:
                dependencies["dev_dependencies"] = list(config["devDependencies"].keys())
        
        elif build_type == "pip":
            if "requirements" in config:
                dependencies["direct"] = config["requirements"]
        
        elif build_type == "cargo":
            if "dependencies" in config:
                dependencies["direct"] = list(config["dependencies"].keys())
        
        return dependencies
    
    async def _detect_languages(self, repo_path: str) -> Dict[str, Any]:
        """Detect programming languages used in the repository."""
        languages = {
            "primary": "unknown",
            "all": [],
            "file_counts": {},
            "frameworks": []
        }
        
        # Language file extensions
        lang_extensions = {
            "c": [".c", ".h"],
            "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
            "python": [".py", ".pyx", ".pyi"],
            "java": [".java"],
            "javascript": [".js", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "go": [".go"],
            "rust": [".rs"],
            "php": [".php"],
            "ruby": [".rb"],
            "swift": [".swift"],
            "kotlin": [".kt", ".kts"],
            "scala": [".scala"],
            "csharp": [".cs"],
            "fsharp": [".fs"],
            "dart": [".dart"],
            "r": [".r", ".R"],
            "matlab": [".m"],
            "fortran": [".f", ".f90", ".f95"],
            "assembly": [".asm", ".s", ".S"]
        }
        
        # Count files by language
        lang_counts = {}
        
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.startswith('.'):
                    continue
                
                file_ext = os.path.splitext(file)[1].lower()
                
                for lang, extensions in lang_extensions.items():
                    if file_ext in extensions:
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                        break
        
        # Determine primary language
        if lang_counts:
            languages["primary"] = max(lang_counts, key=lang_counts.get)
            languages["all"] = list(lang_counts.keys())
            languages["file_counts"] = lang_counts
        
        # Detect frameworks
        frameworks = await self._detect_frameworks(repo_path, languages["primary"])
        languages["frameworks"] = frameworks
        
        return languages
    
    async def _detect_frameworks(self, repo_path: str, primary_lang: str) -> List[str]:
        """Detect frameworks used in the project."""
        frameworks = []
        
        # Framework detection patterns
        framework_patterns = {
            "python": {
                "django": ["django", "manage.py"],
                "flask": ["flask", "app.py"],
                "fastapi": ["fastapi", "uvicorn"],
                "pytorch": ["torch", "pytorch"],
                "tensorflow": ["tensorflow", "tf"],
                "scikit-learn": ["sklearn", "scikit-learn"]
            },
            "javascript": {
                "react": ["react", "jsx"],
                "vue": ["vue", "vue.js"],
                "angular": ["angular", "ng-"],
                "express": ["express"],
                "next": ["next"],
                "nuxt": ["nuxt"]
            },
            "java": {
                "spring": ["spring", "spring-boot"],
                "hibernate": ["hibernate"],
                "maven": ["maven", "pom.xml"],
                "gradle": ["gradle", "build.gradle"]
            },
            "cpp": {
                "boost": ["boost"],
                "qt": ["qt", "q_"],
                "opencv": ["opencv", "cv::"],
                "eigen": ["eigen"]
            }
        }
        
        patterns = framework_patterns.get(primary_lang, {})
        
        for framework, keywords in patterns.items():
            for keyword in keywords:
                # Search in files
                for root, _, files in os.walk(repo_path):
                    for file in files:
                        if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.hpp')):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                                    if keyword.lower() in content.lower():
                                        frameworks.append(framework)
                                        break
                            except:
                                continue
                    if framework in frameworks:
                        break
        
        return list(set(frameworks))  # Remove duplicates
    
    async def _infer_purpose(self, repo_path: str, structure: Dict[str, Any], languages: Dict[str, Any]) -> Dict[str, Any]:
        """Infer the purpose of the project."""
        purpose = {
            "type": "unknown",
            "description": "",
            "category": "unknown",
            "confidence": 0.0
        }
        
        # Analyze README and documentation
        readme_content = await self._extract_readme_content(repo_path)
        
        # Create prompt for LLM analysis
        prompt = f"""
        Analyze this software project and determine its purpose:
        
        Repository structure:
        - Total files: {structure.get('total_files', 0)}
        - File types: {list(structure.get('file_types', {}).keys())}
        - Primary language: {languages.get('primary', 'unknown')}
        - Frameworks: {languages.get('frameworks', [])}
        
        README content:
        {readme_content[:1000]}
        
        Please provide:
        1. Project type (e.g., web application, library, CLI tool, data analysis, etc.)
        2. Brief description of what the project does
        3. Category (e.g., development tools, data science, web development, etc.)
        4. Confidence level (0-1)
        
        Respond in JSON format:
        {{
            "type": "project_type",
            "description": "brief description",
            "category": "category",
            "confidence": 0.8
        }}
        """
        
        try:
            request = LLMRequest(
                prompt=prompt,
                system_message="You are an expert software analyst. Analyze the given project information and provide accurate classification.",
                temperature=0.1
            )
            
            response = await self.call_llm(request)
            
            if response.content:
                # Try to parse JSON response
                try:
                    result = json.loads(response.content)
                    purpose.update(result)
                except json.JSONDecodeError:
                    # Fallback: extract information from text
                    purpose["description"] = response.content[:200]
            
        except Exception as e:
            self.logger.warning(f"Error inferring purpose with LLM: {e}")
            # Fallback analysis
            purpose = await self._fallback_purpose_analysis(structure, languages)
        
        return purpose
    
    async def _extract_readme_content(self, repo_path: str) -> str:
        """Extract content from README files."""
        readme_files = ["README", "README.md", "README.txt", "README.rst"]
        content = ""
        
        for readme_file in readme_files:
            readme_path = os.path.join(repo_path, readme_file)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        break
                except:
                    continue
        
        return content
    
    async def _fallback_purpose_analysis(self, structure: Dict[str, Any], languages: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback purpose analysis without LLM."""
        purpose = {
            "type": "unknown",
            "description": "",
            "category": "unknown",
            "confidence": 0.3
        }
        
        primary_lang = languages.get("primary", "unknown")
        frameworks = languages.get("frameworks", [])
        
        # Simple heuristics
        if "web" in frameworks or primary_lang in ["javascript", "typescript", "python"]:
            purpose["type"] = "web_application"
            purpose["category"] = "web_development"
            purpose["confidence"] = 0.6
        
        elif primary_lang in ["c", "cpp"]:
            purpose["type"] = "system_software"
            purpose["category"] = "system_development"
            purpose["confidence"] = 0.5
        
        elif primary_lang == "python" and any(fw in frameworks for fw in ["pytorch", "tensorflow", "sklearn"]):
            purpose["type"] = "machine_learning"
            purpose["category"] = "data_science"
            purpose["confidence"] = 0.7
        
        return purpose
    
    async def _extract_build_instructions(self, repo_path: str, build_system: Dict[str, Any]) -> Dict[str, Any]:
        """Extract build instructions from documentation."""
        instructions = {
            "commands": build_system.get("commands", []),
            "documentation": "",
            "prerequisites": []
        }
        
        # Extract from README
        readme_content = await self._extract_readme_content(repo_path)
        
        # Look for build instructions in README
        build_sections = ["## Build", "## Installation", "## Setup", "## Getting Started"]
        for section in build_sections:
            if section in readme_content:
                start_idx = readme_content.find(section)
                end_idx = readme_content.find("##", start_idx + 1)
                if end_idx == -1:
                    end_idx = len(readme_content)
                
                instructions["documentation"] = readme_content[start_idx:end_idx]
                break
        
        return instructions
    
    async def _extract_test_instructions(self, repo_path: str, build_system: Dict[str, Any]) -> Dict[str, Any]:
        """Extract test instructions from documentation."""
        instructions = {
            "commands": [],
            "documentation": "",
            "test_files": []
        }
        
        # Common test commands by build system
        test_commands_map = {
            "npm": ["npm test", "npm run test"],
            "pip": ["python -m pytest", "python -m unittest"],
            "maven": ["mvn test"],
            "gradle": ["gradle test"],
            "cargo": ["cargo test"],
            "go": ["go test ./..."],
            "make": ["make test", "make check"]
        }
        
        build_type = build_system.get("type", "unknown")
        instructions["commands"] = test_commands_map.get(build_type, [])
        
        # Find test files
        test_patterns = ["test", "tests", "spec", "specs"]
        for root, _, files in os.walk(repo_path):
            for file in files:
                if any(pattern in file.lower() for pattern in test_patterns):
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    instructions["test_files"].append(rel_path)
        
        return instructions