# modules/tools/file_tools.py
"""
File system operations - read, write, search, manage files and directories.
"""

import shutil
import zipfile
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import List
from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> str:
    """
    Read and return the contents of a file.
    
    Args:
        file_path: Absolute or relative path to the file
    
    Returns:
        File contents as string, or error message.
    """
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f" File not found: {file_path}"
        if not path.is_file():
            return f" Not a file: {file_path}"
        
        size = path.stat().st_size
        if size > 5 * 1024 * 1024:  # 5MB limit
            return f" File too large ({size / 1e6:.1f}MB). Max 5MB."
        
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        return f" [{path.name}] ({size} bytes):\n\n{content}"
    except PermissionError:
        return f" Permission denied: {file_path}"
    except Exception as e:
        return f" Error reading file: {str(e)}"


@tool
def write_file(file_path: str, content: str, overwrite: bool = False) -> str:
    """
    Write content to a file. Creates the file if it doesn't exist.
    
    Args:
        file_path: Path where file should be written
        content: Content to write
        overwrite: Whether to overwrite if file exists (default False)
    
    Returns:
        Status message.
    """
    try:
        path = Path(file_path).expanduser().resolve()
        
        if path.exists() and not overwrite:
            return f" File already exists: {file_path}. Set overwrite=True to replace."
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return f" Written {len(content)} characters to: {path}"
    except PermissionError:
        return f" Permission denied: {file_path}"
    except Exception as e:
        return f" Write failed: {str(e)}"


@tool
def list_directory(directory_path: str = ".", show_hidden: bool = False) -> str:
    """
    List contents of a directory with file sizes and modification times.
    
    Args:
        directory_path: Path to directory (default: current directory)
        show_hidden: Whether to show hidden files starting with '.' (default False)
    
    Returns:
        Formatted directory listing.
    """
    try:
        path = Path(directory_path).expanduser().resolve()
        
        if not path.exists():
            return f" Directory not found: {directory_path}"
        if not path.is_dir():
            return f" Not a directory: {directory_path}"
        
        entries = []
        for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if not show_hidden and item.name.startswith("."):
                continue
            
            stat = item.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            if item.is_dir():
                entries.append(f" {item.name}/")
            else:
                size = stat.st_size
                size_str = f"{size}B" if size < 1024 else f"{size/1024:.1f}KB" if size < 1e6 else f"{size/1e6:.1f}MB"
                entries.append(f" {item.name:<40} {size_str:<10} {mod_time}")
        
        header = f" {path} ({len(entries)} items)"
        return header + "\n" + "\n".join(entries) if entries else header + "\n(empty)"
    except PermissionError:
        return f"Permission denied: {directory_path}"
    except Exception as e:
        return f" Error listing directory: {str(e)}"


@tool
def create_directory(directory_path: str) -> str:
    """
    Create a directory (including all parent directories).
    
    Args:
        directory_path: Path of the directory to create
    
    Returns:
        Status message.
    """
    try:
        path = Path(directory_path).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return f"✅ Directory created: {path}"
    except PermissionError:
        return f"❌ Permission denied: {directory_path}"
    except Exception as e:
        return f"❌ Failed to create directory: {str(e)}"


@tool
def delete_file(file_path: str, confirm: bool = False) -> str:
    """
    Delete a file or directory.
    
    Args:
        file_path: Path to file or directory to delete
        confirm: Must be True to proceed (safety check)
    
    Returns:
        Status message.
    """
    if not confirm:
        return "⚠️ Set confirm=True to delete. This cannot be undone."
    
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"❌ Not found: {file_path}"
        
        if path.is_file():
            path.unlink()
            return f"✅ Deleted file: {path}"
        elif path.is_dir():
            shutil.rmtree(path)
            return f"✅ Deleted directory: {path}"
    except PermissionError:
        return f"❌ Permission denied: {file_path}"
    except Exception as e:
        return f"❌ Delete failed: {str(e)}"


@tool
def move_file(source_path: str, destination_path: str) -> str:
    """
    Move or rename a file or directory.
    
    Args:
        source_path: Current path of the file/directory
        destination_path: New path/location
    
    Returns:
        Status message.
    """
    try:
        src = Path(source_path).expanduser().resolve()
        dst = Path(destination_path).expanduser().resolve()
        
        if not src.exists():
            return f" Source not found: {source_path}"
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return f"Moved: {src} → {dst}"
    except Exception as e:
        return f" Move failed: {str(e)}"


@tool
def copy_file(source_path: str, destination_path: str) -> str:
    """
    Copy a file or directory.
    
    Args:
        source_path: Path to the file/directory to copy
        destination_path: Destination path
    
    Returns:
        Status message.
    """
    try:
        src = Path(source_path).expanduser().resolve()
        dst = Path(destination_path).expanduser().resolve()
        
        if not src.exists():
            return f" Source not found: {source_path}"
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        if src.is_file():
            shutil.copy2(str(src), str(dst))
        else:
            shutil.copytree(str(src), str(dst))
        
        return f"Copied: {src} → {dst}"
    except Exception as e:
        return f" Copy failed: {str(e)}"


@tool
def search_files(query: str, directory: str = "~", extension: str = "") -> str:
    """
    Search for files matching a name pattern in a directory.
    
    Args:
        query: Filename pattern to search for (e.g., '*.py', 'report*')
        directory: Directory to search in (default: home directory)
        extension: Optional file extension filter (e.g., '.pdf', '.txt')
    
    Returns:
        List of matching files.
    """
    try:
        base = Path(directory).expanduser().resolve()
        pattern = f"*{query}*{extension}" if extension else f"*{query}*"
        
        matches = []
        for match in base.rglob(pattern):
            if not any(part.startswith('.') for part in match.parts[-3:]):
                matches.append(str(match))
            if len(matches) >= 50:
                break
        
        if not matches:
            return f"No files found matching '{query}' in {base}"
        
        result = f"Found {len(matches)} file(s):\n"
        result += "\n".join(f"  {m}" for m in matches[:30])
        if len(matches) > 30:
            result += f"\n  ... and {len(matches) - 30} more"
        return result
    except Exception as e:
        return f" Search failed: {str(e)}"


@tool
def get_file_info(file_path: str) -> str:
    """
    Get detailed metadata about a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File metadata including size, dates, type, permissions.
    """
    try:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f" Not found: {file_path}"
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        lines = [
            f" File: {path.name}",
            f" Location: {path.parent}",
            f" Size: {stat.st_size:,} bytes ({stat.st_size / 1024:.2f} KB)",
            f"  Type: {mime_type or 'unknown'}",
            f" Created:  {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
            f" Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            f" Accessed: {datetime.fromtimestamp(stat.st_atime).strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f" Error getting file info: {str(e)}"


@tool
def zip_files(output_path: str, file_paths: List[str]) -> str:
    """
    Compress files into a ZIP archive.
    
    Args:
        output_path: Path where the ZIP file will be saved
        file_paths: List of file/directory paths to compress
    
    Returns:
        Status message with archive details.
    """
    try:
        out = Path(output_path).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
            for fp in file_paths:
                p = Path(fp).expanduser().resolve()
                if p.is_file():
                    zf.write(p, p.name)
                    count += 1
                elif p.is_dir():
                    for sub in p.rglob("*"):
                        if sub.is_file():
                            zf.write(sub, sub.relative_to(p.parent))
                            count += 1
        
        size = out.stat().st_size
        return f"Created ZIP: {out}\n   Files: {count} | Size: {size / 1024:.1f} KB"
    except Exception as e:
        return f" Zip failed: {str(e)}"
