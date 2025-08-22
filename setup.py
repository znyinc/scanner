#!/usr/bin/env python3
"""
Setup script for Stock Scanner project
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return False

def setup_backend():
    """Set up the backend environment"""
    print("Setting up backend...")
    backend_dir = Path("backend")
    
    # Create virtual environment
    if not (backend_dir / "venv").exists():
        print("Creating virtual environment...")
        if not run_command("python -m venv venv", cwd=backend_dir):
            print("Failed to create virtual environment")
            return False
    
    # Install dependencies
    print("Installing Python dependencies...")
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip install -r requirements.txt"
    else:  # macOS/Linux
        pip_cmd = "venv/bin/pip install -r requirements.txt"
    
    if not run_command(pip_cmd, cwd=backend_dir):
        print("Failed to install Python dependencies")
        return False
    
    print("Backend setup complete!")
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("Setting up frontend...")
    frontend_dir = Path("frontend")
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    if not run_command("npm install", cwd=frontend_dir):
        print("Failed to install Node.js dependencies")
        return False
    
    print("Frontend setup complete!")
    return True

def setup_database():
    """Set up the database"""
    print("Setting up database...")
    
    # Start PostgreSQL container
    print("Starting PostgreSQL container...")
    if not run_command("docker-compose up -d postgres"):
        print("Failed to start PostgreSQL container")
        return False
    
    print("Database setup complete!")
    return True

def main():
    """Main setup function"""
    print("Stock Scanner Project Setup")
    print("=" * 30)
    
    # Check if required tools are available
    required_tools = ["python", "node", "npm", "docker"]
    for tool in required_tools:
        if not run_command(f"{tool} --version"):
            print(f"Error: {tool} is not installed or not in PATH")
            sys.exit(1)
    
    # Setup components
    success = True
    success &= setup_backend()
    success &= setup_frontend()
    success &= setup_database()
    
    if success:
        print("\n" + "=" * 30)
        print("Setup completed successfully!")
        print("\nTo start the application:")
        print("1. Backend: cd backend && uvicorn app.main:app --reload")
        print("2. Frontend: cd frontend && npm start")
        print("3. Visit http://localhost:3000")
    else:
        print("\nSetup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()