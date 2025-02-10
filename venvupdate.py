# venvupdate.py
import os
import subprocess
import sys

def update_venv_and_requirements(venv_path="venv"):
    """
    Ensures the virtual environment exists, installs dependencies from
    requirements.txt, and updates the requirements file with the latest dependencies.
    """

    if not os.path.exists(venv_path):
        print("📦 Virtual environment not found! Creating one...")
        subprocess.run([sys.executable, "-m", "venv", venv_path])

    pip_exec = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")

    print("📦 Checking dependencies...")
    subprocess.run([pip_exec, "install", "-r", "requirements.txt"])

    print("🔄 Updating requirements.txt...")
    with open("requirements.txt", "w") as req_file:
        subprocess.run([pip_exec, "freeze"], stdout=req_file)

    print("✅ Virtual environment is up to date!")
