
import subprocess

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, executable='/bin/bash')
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def create_conda_env(env_name, python_version, cmake_version):
    command = f"conda create -n {env_name} python={python_version} cmake={cmake_version} -y"
    return execute_command(command)

if __name__ == "__main__":
    print(create_conda_env("cut3r", "3.11", "3.14.0"))