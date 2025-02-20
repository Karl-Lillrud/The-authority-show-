import os
import subprocess
import sys
import shutil
from pathlib import Path

# Define the virtual environment path
VENV_PATH = Path("venv")

"""
    Checks if the virtual environment contains necessary activation files.
    Returns True if valid, False otherwise.
"""
def check_venv_files():
    
    if os.name == "nt":

        return (VENV_PATH / "Scripts" / "activate.bat").exists()
    
    else:

        return (VENV_PATH / "bin" / "activate").exists()

""" Creates a new virtual environment. """
def create_virtual_environment():
    
    try:

        print("Creating a new virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_PATH)], check=True)
        
    except subprocess.CalledProcessError:

        print("Failed to create virtual environment.")
        sys.exit(1)

""" Removes an invalid or incomplete virtual environment. """
def remove_invalid_venv():
    
    if VENV_PATH.exists():

        print("Removing invalid virtual environment...")
        shutil.rmtree(VENV_PATH)

""" Installs dependencies from `requirements.txt` if it exists. """
def install_dependencies():

    req_file = Path("requirements.txt")

    pip_exec = (

        VENV_PATH / "Scripts" / "pip.exe"
        if os.name == "nt"
        else VENV_PATH / "bin" / "pip"
        
    )

    if not req_file.exists() or req_file.stat().st_size == 0:

        print("No valid requirements.txt found. Skipping installation.")
        return

    print("Installing dependencies from requirements.txt...")
    result = subprocess.run([str(pip_exec), "install", "-r", str(req_file)], capture_output=True, text=True)

    for line in result.stdout.splitlines():

        if "Requirement already satisfied" not in line:
            print(line)

""" Updates `requirements.txt` with installed packages. """
def update_requirements():
    
    pip_exec = (
        VENV_PATH / "Scripts" / "pip.exe"
        if os.name == "nt"
        else VENV_PATH / "bin" / "pip"
    )

    print("Updating requirements.txt...")

    with open("requirements.txt", "w") as req_file:

        subprocess.run([str(pip_exec), "freeze"], stdout=req_file, check=True)

"""
    Ensures the virtual environment exists.
    - If missing or invalid, it will be recreated.
    - Installs dependencies.
    - Updates `requirements.txt`.
"""
def update_venv_and_requirements():
    
    print("Checking virtual environment...")
    
    # Check if virtual environment exists
    if VENV_PATH.exists() and check_venv_files():

        print("Valid virtual environment found. Skipping recreation...")

    else:

        # Remove and recreate the virtual environment if invalid
        remove_invalid_venv()
        create_virtual_environment()

    # Install required dependencies
    install_dependencies()
    
    # Update the requirements.txt file with installed packages
    update_requirements()
    
    print("Virtual environment is up to date!")

# Run the virtual environment update process
if __name__ == "__main__":
    
    update_venv_and_requirements()