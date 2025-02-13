import os
import subprocess
import sys
import shutil

def check_venv_files(venv_path="venv"):
    """
    Checks if the virtual environment has the necessary files (Scripts or bin).
    Returns True if the venv folder is valid, False if not.
    """
    if os.name == "nt":
        # For Windows, check the 'Scripts' folder
        return os.path.exists(os.path.join(venv_path, "Scripts", "activate.bat"))
    else:
        # For non-Windows (Unix-like), check the 'bin' folder
        return os.path.exists(os.path.join(venv_path, "bin", "activate"))

def update_venv_and_requirements(venv_path="venv"):
    """
    Ensures the virtual environment exists. If missing or corrupted, recreates it.
    Installs dependencies from requirements.txt and updates the requirements file.
    """

    # Step 1: Check if the venv exists and has necessary files
    if os.path.exists(venv_path) and check_venv_files(venv_path):
        print("📦 Valid virtual environment found. Skipping recreation...")
    else:
        # Step 2: If venv doesn't exist or is missing necessary files, delete the existing venv
        if os.path.exists(venv_path):
            print("🗑️ Removing invalid or incomplete virtual environment...")
            shutil.rmtree(venv_path)  # Deletes the entire venv folder

        # Step 3: Create a new virtual environment (only the relevant files)
        print("📦 Creating a new virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Step 4: Determine the correct pip executable inside venv
    pip_exec = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")

    # Step 5: Ensure pip is installed
    print("🚀 Ensuring pip is installed...")
    subprocess.run([sys.executable, "-m", "ensurepip"], check=True)

    # Step 6: Install dependencies from requirements.txt (if it exists)
    if os.path.exists("requirements.txt") and os.path.getsize("requirements.txt") > 0:
        print("📦 Installing dependencies from requirements.txt...")
        subprocess.run([pip_exec, "install", "-r", "requirements.txt"], check=True)
    else:
        print("⚠️ No valid requirements.txt found. Skipping installation.")

    # Step 7: Update requirements.txt with installed packages
    print("🔄 Updating requirements.txt...")
    with open("requirements.txt", "w") as req_file:
        subprocess.run([pip_exec, "freeze"], stdout=req_file, check=True)

    print("✅ Virtual environment is up to date!")

# Run the function when the script is executed
if __name__ == "__main__":
    update_venv_and_requirements()
