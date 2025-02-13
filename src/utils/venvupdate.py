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
        return os.path.exists(os.path.join(venv_path, "Scripts", "activate.bat"))
    else:
        return os.path.exists(os.path.join(venv_path, "bin", "activate"))

def get_installed_packages(venv_path="venv"):
    """
    Returns a set of installed packages in the virtual environment.
    """
    pip_exec = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
    result = subprocess.run([pip_exec, "freeze"], capture_output=True, text=True)
    installed_packages = result.stdout.splitlines()
    return {pkg.split("==")[0].lower() for pkg in installed_packages}

def update_venv_and_requirements(venv_path="venv", req_file="requirements.txt"):
    """
    Ensures the virtual environment exists. If missing or corrupted, recreates it.
    Installs missing dependencies from requirements.txt and updates the requirements file.
    """

    # Step 1: Check if the venv exists and has necessary files
    if os.path.exists(venv_path) and check_venv_files(venv_path):
        print("📦 Valid virtual environment found. Skipping recreation...")
    else:
        if os.path.exists(venv_path):
            print("🗑️ Removing invalid or incomplete virtual environment...")
            shutil.rmtree(venv_path)
        print("📦 Creating a new virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)

    # Step 2: Ensure pip is installed
    pip_exec = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
    print("🚀 Ensuring pip is installed...")
    subprocess.run([sys.executable, "-m", "ensurepip"], check=True)

    # Step 3: Install dependencies from requirements.txt if it exists
    if os.path.exists(req_file) and os.path.getsize(req_file) > 0:
        print(f"📦 Installing dependencies from {req_file}...")

        # Read the required packages from requirements.txt
        with open(req_file) as f:
            required_packages = {line.strip().split("==")[0].lower() for line in f.readlines()}

        # Get the currently installed packages
        installed_packages = get_installed_packages(venv_path)

        # Find missing packages (that are required but not installed)
        missing_packages = required_packages - installed_packages
        
        if missing_packages:
            print(f"⚙️ Installing missing packages: {', '.join(missing_packages)}")
            subprocess.run([pip_exec, "install", *missing_packages], check=True)
        else:
            print("✅ All required packages are already installed.")

    else:
        print("⚠️ No valid requirements.txt found or it's empty. Skipping installation.")

    # Step 4: Update requirements.txt with installed packages
    print("🔄 Updating requirements.txt with current installed packages...")
    with open(req_file, "w") as req_file:
        subprocess.run([pip_exec, "freeze"], stdout=req_file, check=True)

    print("✅ Virtual environment is up to date!")

# Run the function when the script is executed
if __name__ == "__main__":
    update_venv_and_requirements()
