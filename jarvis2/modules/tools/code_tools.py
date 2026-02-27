# modules/tools/code_tools.py
"""
Code execution and package management tools.
These are powerful — use with care.
"""

import subprocess
import sys
import os
import tempfile
from langchain_core.tools import tool


@tool
def run_python_code(code: str, timeout: int = 30) -> str:
    """
    Execute Python code and return the output.
    Use this for calculations, data processing, or quick scripts.
    
    Args:
        code: Python code to execute
        timeout: Max execution time in seconds (default 30)
    
    Returns:
        stdout/stderr output from the code execution.
    """
    # Write to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~")
        )

        output = ""
        if result.stdout:
            output += f"📤 Output:\n{result.stdout}"
        if result.stderr:
            output += f"\n⚠️ Errors:\n{result.stderr}"
        if result.returncode != 0:
            output += f"\n❌ Exited with code {result.returncode}"

        return output.strip() or "✅ Code executed (no output)"
    except subprocess.TimeoutExpired:
        return f"❌ Code timed out after {timeout} seconds."
    except Exception as e:
        return f"❌ Execution failed: {str(e)}"
    finally:
        os.unlink(tmp_path)


@tool
def run_shell_command(command: str, working_directory: str = "~", timeout: int = 30) -> str:
    """
    Run a shell command and return the output.
    
    Args:
        command: Shell command to run
        working_directory: Directory to run the command in (default: home)
        timeout: Max execution time in seconds (default 30)
    
    Returns:
        Command output (stdout and stderr).
    """
    # Safety: Block destructive commands
    blocked = ["rm -rf /", "mkfs", "> /dev/sda", "dd if=/dev/zero"]
    if any(b in command for b in blocked):
        return f"❌ Blocked: This command is potentially destructive."
    
    cwd = os.path.expanduser(working_directory)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n⚠️ stderr: {result.stderr}"
        if result.returncode != 0:
            output += f"\n❌ Exit code: {result.returncode}"
        
        return output.strip() or "✅ Command executed (no output)"
    except subprocess.TimeoutExpired:
        return f"❌ Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"❌ Command failed: {str(e)}"


@tool
def install_package(package_name: str) -> str:
    """
    Install a Python package using pip.
    
    Args:
        package_name: Name of the package to install (e.g., 'requests', 'pandas')
    
    Returns:
        Installation output.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name, "--quiet"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            return f" Successfully installed: {package_name}"
        else:
            return f" Failed to install {package_name}:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return f" Installation timed out for: {package_name}"
    except Exception as e:
        return f" Install failed: {str(e)}"
