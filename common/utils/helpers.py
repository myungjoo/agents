"""
Helper utility functions for the AI Agent System.

Provides common utility functions used across different components
including file operations, text processing, and system utilities.
"""

import os
import re
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
import subprocess
import psutil
import json
import yaml
from datetime import datetime, timedelta
import asyncio
import aiofiles
import aiohttp


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists and return Path object."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_directory(path: Union[str, Path], max_age_days: int = 7):
    """Clean old files from directory."""
    path = Path(path)
    if not path.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    
    for file_path in path.rglob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                except OSError:
                    pass  # Ignore errors when deleting files


def get_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Get hash of file contents."""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_system_info() -> Dict[str, Any]:
    """Get current system information."""
    return {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent
        },
        "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
    }


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to be filesystem safe."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized


def extract_repo_info(repository_url: str) -> Dict[str, str]:
    """Extract repository information from URL."""
    # Handle GitHub URLs
    github_pattern = r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(github_pattern, repository_url)
    
    if match:
        owner, repo = match.groups()
        return {
            "platform": "github",
            "owner": owner,
            "repository": repo,
            "full_name": f"{owner}/{repo}",
            "api_url": f"https://api.github.com/repos/{owner}/{repo}",
            "clone_url": f"https://github.com/{owner}/{repo}.git"
        }
    
    # Handle generic Git URLs
    git_pattern = r'(https?://[^/]+)/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(git_pattern, repository_url)
    
    if match:
        base_url, owner, repo = match.groups()
        return {
            "platform": "generic",
            "owner": owner,
            "repository": repo,
            "full_name": f"{owner}/{repo}",
            "base_url": base_url,
            "clone_url": repository_url
        }
    
    return {"platform": "unknown", "url": repository_url}


def detect_language(file_path: Union[str, Path]) -> Optional[str]:
    """Detect programming language from file extension."""
    file_path = Path(file_path)
    ext = file_path.suffix.lower()
    
    language_map = {
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.cc': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        '.py': 'python',
        '.java': 'java',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.go': 'go',
        '.rs': 'rust',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.fish': 'shell',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.R': 'r',
        '.m': 'matlab',
        '.pl': 'perl',
        '.lua': 'lua',
        '.vim': 'vim',
        '.sql': 'sql'
    }
    
    return language_map.get(ext)


def count_lines_of_code(file_path: Union[str, Path]) -> Dict[str, int]:
    """Count lines of code in a file."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"total": 0, "code": 0, "comments": 0, "blank": 0}
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception:
        return {"total": 0, "code": 0, "comments": 0, "blank": 0}
    
    total_lines = len(lines)
    blank_lines = 0
    comment_lines = 0
    
    language = detect_language(file_path)
    
    # Define comment patterns for different languages
    comment_patterns = {
        'c': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'cpp': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'python': [r'^\s*#.*$', r'^\s*""".*""".*$', r"^\s*'''.*'''.*$"],
        'java': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'javascript': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'typescript': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'shell': [r'^\s*#.*$'],
        'ruby': [r'^\s*#.*$'],
        'go': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
        'rust': [r'^\s*//.*$', r'^\s*/\*.*\*/\s*$'],
    }
    
    patterns = comment_patterns.get(language, [])
    
    for line in lines:
        line = line.strip()
        
        if not line:
            blank_lines += 1
        elif any(re.match(pattern, line) for pattern in patterns):
            comment_lines += 1
    
    code_lines = total_lines - blank_lines - comment_lines
    
    return {
        "total": total_lines,
        "code": code_lines,
        "comments": comment_lines,
        "blank": blank_lines
    }


async def run_command_async(command: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Run command asynchronously and return exit code, stdout, stderr."""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        
        return (
            process.returncode,
            stdout.decode('utf-8', errors='ignore'),
            stderr.decode('utf-8', errors='ignore')
        )
        
    except asyncio.TimeoutError:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)


def run_command_sync(command: List[str], cwd: Optional[Path] = None, timeout: int = 300) -> Tuple[int, str, str]:
    """Run command synchronously and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -1, "", str(e)


def parse_git_url(url: str) -> Dict[str, str]:
    """Parse git URL and return components."""
    # SSH format: git@github.com:owner/repo.git
    ssh_pattern = r'git@([^:]+):([^/]+)/(.+?)(?:\.git)?$'
    ssh_match = re.match(ssh_pattern, url)
    
    if ssh_match:
        host, owner, repo = ssh_match.groups()
        return {
            "protocol": "ssh",
            "host": host,
            "owner": owner,
            "repository": repo,
            "full_name": f"{owner}/{repo}"
        }
    
    # HTTPS format: https://github.com/owner/repo.git
    https_pattern = r'https://([^/]+)/([^/]+)/(.+?)(?:\.git)?/?$'
    https_match = re.match(https_pattern, url)
    
    if https_match:
        host, owner, repo = https_match.groups()
        return {
            "protocol": "https",
            "host": host,
            "owner": owner,
            "repository": repo,
            "full_name": f"{owner}/{repo}"
        }
    
    return {"protocol": "unknown", "url": url}


async def download_file_async(url: str, file_path: Union[str, Path], chunk_size: int = 8192) -> bool:
    """Download file asynchronously."""
    file_path = Path(file_path)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await f.write(chunk)
                    
                    return True
                else:
                    return False
                    
    except Exception:
        return False


def load_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load JSON file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> bool:
    """Save data to JSON file safely."""
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        return True
    except Exception:
        return False


def load_yaml_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Load YAML file safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def save_yaml_file(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """Save data to YAML file safely."""
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
        
        return True
    except Exception:
        return False


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks from markdown text."""
    code_block_pattern = r'```(\w+)?\n(.*?)\n```'
    matches = re.findall(code_block_pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            "language": language or "text",
            "code": code.strip()
        })
    
    return code_blocks


def create_temp_directory(prefix: str = "ai_agents_") -> Path:
    """Create temporary directory and return path."""
    temp_dir = tempfile.mkdtemp(prefix=prefix)
    return Path(temp_dir)


def cleanup_temp_directory(temp_dir: Union[str, Path]):
    """Clean up temporary directory."""
    temp_dir = Path(temp_dir)
    if temp_dir.exists() and temp_dir.is_dir():
        try:
            shutil.rmtree(temp_dir)
        except OSError:
            pass  # Ignore errors when cleaning up