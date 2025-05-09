import subprocess
import os

def execute_command(command):
    try:
        # Use the command parameter instead of hardcoding
        if isinstance(command, str):
            # When passing a string, use shell=True
            shell_mode = True
            cmd_args = command
        else:
            # When passing a list, use shell=False
            shell_mode = False
            cmd_args = command
            
        print(f"Executing: {cmd_args} (shell={shell_mode})")
        
        result = subprocess.Popen(
            cmd_args,
            shell=shell_mode,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=os.environ.copy(),
        )
        
        # Use communicate() to get the output
        stdout, stderr = result.communicate()
        print(f"Stdout: {stdout}")
        print(f"Stderr: {stderr}")

    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Exception: {str(e)}"

def test_conda_command():
    # Use the actual conda path if needed
    execute_command("D:\\Anaconda\\condabin\\conda.bat env list")


test_conda_command()