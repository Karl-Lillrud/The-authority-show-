import subprocess
import sys

"""
Pip Automation Script

This script simplifies installing and uninstalling Python packages using pip.
It also ensures that `requirements.txt` is updated after every change.

Usage:
    python pip_auto.py install package_name
    python pip_auto.py uninstall package_name
"""

# Ensure the user provides the correct number of arguments
if len(sys.argv) < 3:
    print("Usage: python pip_auto.py install/uninstall package_name")
    sys.exit(1)

# Parse command-line arguments
command = sys.argv[1].lower()
package = sys.argv[2]

# Determine action based on command
if command == "install":
    print(f"Installing package: {package}...")
    subprocess.run(["pip", "install", package], check=True)

elif command == "uninstall":
    print(f"Uninstalling package: {package}...")
    subprocess.run(["pip", "uninstall", "-y", package], check=True)

else:
    print("Invalid command. Use 'install' or 'uninstall'.")
    sys.exit(1)

# Update requirements.txt after installation/uninstallation
print("Updating requirements.txt...")
with open("requirements.txt", "w") as req_file:
    subprocess.run(["pip", "freeze"], stdout=req_file, check=True)

print("Operation completed successfully!")
