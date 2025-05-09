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
        command: The command to execute (string or list).
        cwd: The working directory for the command.

    Returns:
        A dictionary containing the command execution result.
    """
    try:
        # Convert string command to list for better security and argument handling
        # For conda commands in particular, we want to use this approach
        # shell_mode = False
        # if isinstance(command, str):
        #     if command.strip().startswith("conda"):
        #         # Special handling for conda commands
        #         cmd_args = command.split()
        #     else:
        #         # For other commands, we'll keep using shell=True for compatibility
        #         cmd_args = command
        #         shell_mode = True
        # else:
        #     cmd_args = command
        #     shell_mode = False
        # shell_mode = True
        # Run the command with appropriate stdout/stderr capturing
        # if "conda" in command:
        #     command = command.replace("conda", "D:\Anaconda\condabin\conda.bat")
        command = "D:\\Anaconda\\condabin\\conda.bat env list"
        print(command)
        result = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=os.environ.copy(),
        )
        stdout, stderr = result.communicate()
        result.kill()
        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": result.returncode == 0
        }
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
def clone_and_setup_repo(local_dir: str, setup_commands: List[str], current_step: int = 0) -> Dict[str, Any]:
    """
    执行setup_commands中的一条命令，每次调用只执行一条，返回结果和下一个step。

    Args:
        local_dir: 仓库本地路径
        setup_commands: 待执行命令列表
        current_step: 当前要执行的命令索引

    Returns:
        dict: {
            "repo_path": ...,
            "step": 当前执行的step,
            "command": 本次执行的命令,
            "result": 本次命令执行结果,
            "next_step": 下一个step索引（如果有）,
            "finished": 是否全部执行完
        }
    """
    if current_step >= len(setup_commands):
        return {
            "repo_path": local_dir,
            "finished": True,
            "message": "All setup commands have been executed."
        }
    cmd = setup_commands[current_step]
    result = execute_command(cmd, local_dir)
    finished = (current_step == len(setup_commands) - 1)
    return {
        "repo_path": local_dir,
        "step": current_step,
        "command": cmd,
        "result": result,
        "next_step": current_step + 1 if not finished else None,
        "finished": finished
    }
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