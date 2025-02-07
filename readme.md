# Pod Manager

## Overview

Pod Manager is a web application designed to manage and monitor pods efficiently. This project provides a user-friendly interface for organizing, tracking, and maintaining pods in a streamlined manner.

## Features

Pod creation and management

Real-time monitoring

User authentication

Issue tracking and reporting

Responsive web interface

## Technologies Used

Python (Flask)

HTML, CSS, JavaScript

Azure Cosmos Db

Azure KeyVault

GitHub for version control

# Getting Started

Prerequisites

Ensure you have the following installed on your system:

Python (3.x)

pip (Python package manager)

Virtual environment module (venv)

Git

VS Code (recommended)

## How to Start the Web App Locally

## 1. Clone the Repository

## Clone the repository
git clone https://github.com/YOUR-USERNAME/Pod-Manager.git

## Navigate into the project directory
cd Pod-Manager

## Switch to the development branch
git checkout dev

## 2. Set Up the Virtual Environment

## Delete existing virtual environment if present
rm -rf venv  # On Linux/macOS
del venv /s /q  # On Windows (Command Prompt)

## Create a new virtual environment
python -m venv venv

## Activate the virtual environment
## On Windows (PowerShell)
.\venv\Scripts\activate
## On macOS/Linux
source venv/bin/activate

## (If activation fails in PowerShell, run this command first)
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope Process

## 3. Install Dependencies

pip install -r requirements.txt

## 4. Start the Web Application

python app.py

## 5. Open in Browser

Open your browser and visit:

http://localhost:8000

# GitHub Workflow

## 1. Clone and Set Up the Repository

Clone the dev branch using VS Code

Navigate to the Issues tab on GitHub

Assign yourself to an issue

## 2. Create a Feature Branch

Click on "Create a branch"

Change the branch source to dev

Name your branch appropriately (e.g., feature-xyz)

Copy the Git commands provided and execute them in the VS Code terminal

## 3. Make Changes and Push

Work on your feature/issue

Commit your changes using meaningful commit messages

Push your changes to GitHub

## 4. Open a Pull Request

Open a PR from your feature branch to dev

Ensure your changes are reviewed before merging

## 5. Merge to dev

Once approved, merge your branch into dev

If VS Code suggests comparing with main, ensure the comparison is with dev

## We welcome contributions! Follow these steps to contribute:

Fork the repository

Create a new branch (feature-xyz)

Implement your feature or bug fix

Commit and push your changes

Open a pull request against dev

# Contact

For any issues or inquiries, feel free to reach out via GitHub Issues or email the project maintainers.

