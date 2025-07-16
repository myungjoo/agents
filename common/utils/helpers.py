#!/usr/bin/env python3
"""
Helper utility functions for AI Agent System
"""

import asyncio
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiofiles


def parse_size_string(size_str: str) -> int:
    """
    Parse size string to bytes
    
    Args:
        size_str: Size string like "100MB", "1GB", etc.
        
    Returns:
        Size in bytes
    """
    size_str = size_str.upper().strip()
    
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4
    }
    
    for unit, multiplier in multipliers.items():
        if size_str.endswith(unit):
            number = size_str[:-len(unit)].strip()
            try:
                return int(float(number) * multiplier)
            except ValueError:
                break
    
    # If no unit specified, assume bytes
    try:
        return int(size_str)
    except ValueError:
        raise ValueError(f"Invalid size string: {size_str}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace dangerous characters
    dangerous_chars = '<>:"/\\|?*'
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure it's not empty
    if not filename:
        filename = "unnamed"
    
    return filename


async def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file asynchronously
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hex digest of file hash
    """
    hash_obj = hashlib.new(algorithm)
    
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(8192):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def get_directory_size(path: Union[str, Path]) -> int:
    """
    Get total size of directory and all its contents
    
    Args:
        path: Directory path
        
    Returns:
        Total size in bytes
    """
    path = Path(path)
    total_size = 0
    
    for item in path.rglob('*'):
        if item.is_file():
            try:
                total_size += item.stat().st_size
            except (OSError, IOError):
                # Skip files that can't be accessed
                pass
    
    return total_size


async def copy_file_async(src: Union[str, Path], dst: Union[str, Path], chunk_size: int = 64 * 1024) -> None:
    """
    Copy file asynchronously
    
    Args:
        src: Source file path
        dst: Destination file path
        chunk_size: Size of chunks to copy at once
    """
    src_path = Path(src)
    dst_path = Path(dst)
    
    # Create destination directory if it doesn't exist
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(src_path, 'rb') as src_file:
        async with aiofiles.open(dst_path, 'wb') as dst_file:
            while chunk := await src_file.read(chunk_size):
                await dst_file.write(chunk)


def create_temp_directory(prefix: str = "ai_audit_") -> str:
    """
    Create temporary directory
    
    Args:
        prefix: Prefix for directory name
        
    Returns:
        Path to created directory
    """
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_directory(path: Union[str, Path]) -> None:
    """
    Clean up temporary directory
    
    Args:
        path: Path to directory to remove
    """
    path = Path(path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"


def format_file_size(bytes_size: int) -> str:
    """
    Format file size in bytes to human readable string
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


async def run_with_timeout(coro, timeout: float):
    """
    Run coroutine with timeout
    
    Args:
        coro: Coroutine to run
        timeout: Timeout in seconds
        
    Returns:
        Coroutine result
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    return await asyncio.wait_for(coro, timeout=timeout)