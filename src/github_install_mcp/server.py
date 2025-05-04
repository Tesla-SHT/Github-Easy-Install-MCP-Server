"""GitHub repository installation MCP server implementation."""

from fastmcp import FastMCP
import os
import subprocess
import tempfile
import shutil
from typing import List, Dict, Any
import hashlib
import git
import sys

# Create FastMCP instance
mcp = FastMCP(
    "GitHub Easy Install",
    description="Analyze GitHub repositories and automate installation process",
    dependencies=[
        "gitpython",
        "PyGithub",
    ]
)

################# Step 1: System Information Detection ###################
@mcp.tool()
def detect_system_info() -> Dict[str, Any]:
    """
    Detect system information, including OS, Python version, and package manager availability.

    Returns:
        A dictionary containing system information.
    """
    info = {
        "os": os.name,
        "platform": sys.platform,
        "python_version": sys.version,
        "conda_exists": shutil.which("conda") is not None  # Check if conda exists
    }
    return info

################# Step 2: Repository Cloning ###################
def clone_repo(repo_url: str, local_dir: str = None) -> str:
    """
    Clone a GitHub repository and return its path. Reuse the directory if already cloned.

    Args:
        repo_url: The URL of the GitHub repository.
        local_dir: Optional custom local directory to clone the repository.

    Returns:
        The path to the cloned repository.
    """
    # Use the provided local directory or generate a temporary directory
    repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
    temp_dir = local_dir or os.path.join(tempfile.gettempdir(), f"github_install_{repo_hash}")

    if os.path.exists(temp_dir):
        try:
            repo = git.Repo(temp_dir)
            if not repo.bare and repo.remote().url == repo_url:
                repo.git.pull()  # Pull the latest changes
                return temp_dir
        except:
            shutil.rmtree(temp_dir, ignore_errors=True)  # Clean up if the repo is invalid

    os.makedirs(temp_dir, exist_ok=True)
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Failed to clone repository: {str(e)}")

################# Step 3: Repository Analysis ###################
def get_directory_tree(path: str, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
    """
    Generate a tree-like structure of the directory.

    Args:
        path: The directory path.
        prefix: The prefix for the tree structure.
        max_depth: Maximum depth to traverse.
        current_depth: Current depth of traversal.

    Returns:
        A string representing the directory structure.
    """
    if current_depth > max_depth:
        return prefix + "...\n"

    output = ""
    entries = sorted(os.listdir(path))
    filtered_entries = [e for e in entries if not e.startswith(('.git', '__pycache__', 'node_modules', 'venv'))]

    for i, entry in enumerate(filtered_entries):
        is_last = i == len(filtered_entries) - 1
        current_prefix = "└── " if is_last else "├── "
        next_prefix = "    " if is_last else "│   "

        entry_path = os.path.join(path, entry)
        output += prefix + current_prefix + entry + "\n"

        if os.path.isdir(entry_path):
            output += get_directory_tree(entry_path, prefix + next_prefix, max_depth, current_depth + 1)

    return output

@mcp.tool()
def analyze_github_repo(repo_url: str, local_dir: str = None) -> Dict[str, Any]:
    """
    Analyze a GitHub repository and collect installation-related information.

    Args:
        repo_url: The URL of the GitHub repository.
        local_dir: Optional custom local directory to clone the repository.

    Returns:
        A dictionary containing repository analysis results.
    """
    try:
        # Clone the repository to the specified local directory
        repo_path = clone_repo(repo_url, local_dir)
        structure = get_directory_tree(repo_path)

        key_files = {}
        key_file_paths = [
            "README.md", "readme.md", "README.rst",
            "requirements.txt", "environment.yml", "environment.yaml",
            "setup.py", "pyproject.toml", "package.json", "Dockerfile"
        ]

        for file_path in key_file_paths:
            full_path = os.path.join(repo_path, file_path)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        key_files[file_path] = f.read()
                except Exception as e:
                    key_files[file_path] = f"Error reading file: {str(e)}"

        return {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "structure": structure,
            "key_files": key_files
        }
    except Exception as e:
        return {"error": f"Failed to analyze repository: {str(e)}"}

################# Step 4: Environment Setup ###################
def analyze_error(error_text: str) -> List[str]:
    """
    Analyze error text to identify possible causes.

    Args:
        error_text: The error message text.

    Returns:
        A list of possible error causes.
    """
    common_errors = {
        "ModuleNotFoundError": "Missing Python module",
        "ImportError": "Import error, possibly missing dependencies",
        "SyntaxError": "Python syntax error",
        "PermissionError": "Permission error, may require admin privileges",
        "FileNotFoundError": "File not found",
        "ConnectionError": "Connection error, may require network access",
        "pip": {
            "Could not find a version": "Could not find the specified package version",
            "Command errored out": "Command execution error"
        },
        "conda": {
            "PackagesNotFoundError": "Could not find the specified conda package",
            "CondaEnvironmentError": "Conda environment error"
        }
    }

    analysis = []
    for error_type, message in common_errors.items():
        if isinstance(message, dict):
            for sub_error, sub_message in message.items():
                if sub_error in error_text:
                    analysis.append(f"{error_type} - {sub_message}")
        elif error_type in error_text:
            analysis.append(message)

    return analysis if analysis else ["Unrecognized error type"]

def execute_command(command: str, cwd: str = None) -> Dict[str, Any]:
    """
    Execute a shell command and return the result.

    Args:
        command: The command to execute.
        cwd: The working directory for the command.

    Returns:
        A dictionary containing the command execution result.
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=cwd,
            text=True
        )
        stdout, stderr = process.communicate()

        result = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": process.returncode == 0,
            "error_analysis": analyze_error(stderr) if process.returncode != 0 else []
        }
        return result
    except Exception as e:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "error_analysis": ["Exception occurred while executing command"]
        }

@mcp.tool()
def clone_and_setup_repo(local_dir: str, setup_commands: List[str]) -> Dict[str, Any]:
    """
    Set up the environment for a previously cloned GitHub repository using provided commands.

    Args:
        local_dir: The local directory where the repository is cloned.
        setup_commands: A list of setup commands to execute.

    Returns:
        A dictionary containing the results of the setup process.
    """
    try:
        setup_results = []
        all_successful = True

        for cmd in setup_commands:
            cmd_result = execute_command(cmd, local_dir)
            setup_results.append(cmd_result)
            if not cmd_result["success"]:
                all_successful = False

        return {
            "repo_path": local_dir,
            "setup_results": setup_results,
            "all_successful": all_successful
        }
    except Exception as e:
        return {"error": f"Failed to set up repository: {str(e)}"}

@mcp.tool()
def execute_cli_command(command: str, working_directory: str = None) -> Dict[str, Any]:
    """
    Execute a CLI command and return the result.

    Args:
        command: The command to execute.
        working_directory: The working directory for the command.

    Returns:
        A dictionary containing the command execution result.
    """
    return execute_command(command, working_directory)

@mcp.prompt("github_installation_workflow")
def github_installation_prompt(repo_url: str, install_path: str) -> str:
    return f"""
    I would like to install a GitHub repository. Please use the MCP Server tool to complete the following automated installation process:

    GitHub repository information [{repo_url}];  
    Installation location [{install_path}];

    Please execute the following steps, with each command separated by a semicolon instead of &&:

    1. Detect system information, including OS, Python version, and package manager availability.
    2. Clone a GitHub repository and return its path. Reuse the directory if already cloned.
    3. Analyze the cloned GitHub repository and collect installation-related information. Then generate a list of setup commands.
    4. Set up the environment for a previously cloned GitHub repository using provided commands.
    5. Analyze error text to identify possible causes.

    Please display the executed commands and results in detail for each step, and explain the key information in an easy-to-understand manner. 
    Separate all commands with semicolons instead of &&.   
    """

if __name__ == "__main__":
    mcp.run(transport='stdio')