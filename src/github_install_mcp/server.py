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
# 创建 FastMCP 实例
mcp = FastMCP(
    "GitHub Easy Install",
    description="Analyze GitHub repositories and automate installation process",
    dependencies=[
        "gitpython",
        "PyGithub",
    ]
)

def clone_repo(repo_url: str) -> str:
    """克隆仓库并返回路径。如果仓库已经克隆到临时目录中，则重用它。"""
    """ Repo URL example
        ssh://[<user>@]<host>[:<port>]/<path-to-git-repo>
        git://<host>[:<port>]/<path-to-git-repo>
        http[s]://<host>[:<port>]/<path-to-git-repo>
    """
    # 基于仓库URL创建确定性的目录名
    repo_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:12]
    temp_dir = os.path.join(tempfile.gettempdir(), f"github_install_{repo_hash}")
    
    # 如果目录存在且是有效的git仓库，返回它
    if os.path.exists(temp_dir):
        try:
            repo = git.Repo(temp_dir)
            if not repo.bare and repo.remote().url == repo_url:
                # 拉取最新版本
                repo.git.pull()
                return temp_dir
        except:
            # 如果现有仓库有任何错误，清理它
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    # 创建目录并克隆仓库
    os.makedirs(temp_dir, exist_ok=True)
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except Exception as e:
        # 出错时清理
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"无法克隆仓库: {str(e)}")

def get_directory_tree(path: str, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> str:
    """生成类似树的目录结构字符串"""
    if current_depth > max_depth:
        return prefix + "...\n"
        
    output = ""
    entries = os.listdir(path)
    entries.sort()
    
    # 过滤一些常见的大型目录
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

def execute_command(command: str, cwd: str = None) -> Dict[str, Any]:
    """执行命令并返回结果"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=cwd,
            text=True
        )
        stdout, stderr = process.communicate()  # 等待命令完成
        
        result = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "success": process.returncode == 0
        }
        
        # 添加错误分析
        if not result["success"]:
            result["error_analysis"] = analyze_error(stderr)
        else:
            result["error_analysis"] = []
        
        return result
    except Exception as e:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "error_analysis": ["执行命令时发生异常"]
        }

def analyze_error(error_text: str) -> List[str]:
    """简单分析错误文本，找出可能的错误原因"""
    common_errors = {
        "ModuleNotFoundError": "缺少Python模块",
        "ImportError": "导入错误，可能缺少依赖",
        "SyntaxError": "Python语法错误",
        "PermissionError": "权限错误，可能需要管理员权限",
        "FileNotFoundError": "找不到文件",
        "ConnectionError": "连接错误，可能需要网络连接",
        "pip": {
            "Could not find a version": "找不到指定版本的包",
            "Command errored out": "命令执行错误"
        },
        "conda": {
            "PackagesNotFoundError": "找不到指定的conda包",
            "CondaEnvironmentError": "conda环境错误"
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
    
    return analysis if analysis else ["未能识别的错误类型"]

@mcp.tool()
def analyze_github_repo(repo_url: str) -> Dict[str, Any]:
    """
    分析GitHub仓库并收集安装相关信息
    
    Args:
        repo_url: GitHub仓库URL
        
    Returns:
        包含仓库分析结果的字典
    """
    try:
        # 克隆仓库
        repo_path = clone_repo(repo_url)
        
        # 获取目录结构
        structure = get_directory_tree(repo_path)
        
        # 检查关键文件
        results = {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "structure": structure,
            "key_files": {}
        }
        
        # 检查常见的安装相关文件
        key_file_paths = [
            "README.md", "readme.md", "README.rst",
            "requirements.txt",
            "environment.yml", "environment.yaml",
            "setup.py", "pyproject.toml",
            "package.json",
            "Dockerfile"
        ]
        
        for file_path in key_file_paths:
            full_path = os.path.join(repo_path, file_path)
            if os.path.isfile(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        results["key_files"][file_path] = f.read()
                except Exception as e:
                    results["key_files"][file_path] = f"Error reading file: {str(e)}"
        
        return results
            
    except Exception as e:
        return {"error": f"Failed to analyze repository: {str(e)}"}

@mcp.tool()
def execute_cli_command(command: str, working_directory: str = None) -> Dict[str, Any]:
    """
    执行CLI命令并返回结果
    
    Args:
        command: 要执行的命令
        working_directory: 命令执行的工作目录
        
    Returns:
        包含命令执行结果的字典
    """
    return execute_command(command, working_directory)

@mcp.tool()
def clone_and_setup_repo(repo_url: str, setup_commands: List[str]) -> Dict[str, Any]:
    """
    克隆GitHub仓库并根据提供的命令设置环境
    
    Args:
        repo_url: GitHub仓库URL
        setup_commands: 安装命令列表
        
    Returns:
        包含克隆和安装结果的字典
    """
    try:
        # 克隆仓库
        repo_path = clone_repo(repo_url)
        
        # 执行设置命令
        setup_results = []
        all_successful = True
        
        for cmd in setup_commands:
            cmd_result = execute_command(cmd, repo_path)
            setup_results.append(cmd_result)
            if not cmd_result["success"]:
                all_successful = False
        
        return {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "setup_results": setup_results,
            "all_successful": all_successful
        }
            
    except Exception as e:
        return {"error": f"Failed to setup repository: {str(e)}"}

@mcp.tool()
def detect_system_info() -> Dict[str, Any]:
    """
    检测系统信息，包括操作系统、Python版本、可用包管理器等
    
    Returns:
        包含系统信息的字典
    """
    info = {
        "os": os.name,
        "platform": sys.platform,
        "python_version": sys.version
    }
    
    # check if the computer has Nvidia GPU
    has_nvidia_gpu = False
    # try:
    #     nvidia_smi_output = subprocess.check_output("nvidia-smi", shell=True, text=True)
    #     if "NVIDIA-SMI" in nvidia_smi_output:
    #         has_nvidia_gpu = True
    # except Exception as e:
    #     pass
    # info["has_nvidia_gpu"] = has_nvidia_gpu
    #check conda exists
    conda_exists = True
    # try:
    #     conda_output = subprocess.check_output("conda --version", shell=True, text=True)
    #     if "conda" in conda_output:
    #         conda_exists = True
    # except Exception as e:
    #     pass
    info["conda_exists"] = conda_exists
    return info
if __name__ == "__main__":
    mcp.run(transport='stdio')