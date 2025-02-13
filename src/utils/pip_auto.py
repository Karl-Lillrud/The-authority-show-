import subprocess
import sys

if len(sys.argv) < 2:
    print("Usage: python pip_auto.py install/uninstall package_name")
    sys.exit(1)

command = sys.argv[1]
package = sys.argv[2]

if command == "install":
    subprocess.run(["pip", "install", package])
elif command == "uninstall":
    subprocess.run(["pip", "uninstall", "-y", package])

subprocess.run(["pip", "freeze", ">", "requirements.txt"], shell=True)
