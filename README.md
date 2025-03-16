# Wit-Project

## Project Description
Wit-Project is a small version control system inspired by Git, designed for educational purposes. It allows users to understand and implement fundamental version control concepts. The project is entirely written in Python and functions as a command-line interface (CLI) application, supporting basic operations such as repository initialization, file staging, committing, checkout, branching, merging, and visualizing commit history through a graph representation.

## Technologies and Implementation
- **Programming Language:** Python  
- **Execution Environment:** Local file system-based repository  
- **Built-in Libraries:**  
  - `os`, `pathlib`, `shutil`, `sys` – for file and directory management  
  - `datetime` – for commit timestamps  
  - `filecmp` – for detecting changes in files and directories  
  - `random` – for generating unique commit IDs  
- **External Libraries:**  
  - `matplotlib.pyplot` and `networkx` – for visualizing commit history as a graph  
- **Communication Methods:**  
  - No network protocols used – all operations are performed locally  
  - Function calls are executed based on command-line arguments

## Design Principles and Architecture
The project follows a modular approach with a procedural design to mimic the behavior of version control systems:
- **Command-Based Function Implementation:**  
  - Each command (init, add, commit, checkout, branch, merge, graph) is implemented as a separate function, executed based on CLI arguments (similar to the Command Pattern).
- **Custom Error Handling:**  
  - Custom exception classes (`NoWitError`, `CommitIdError`, `CheckoutError`, `DataNotSaved`, `BranchError`, `MergeError`) ensure specific error handling for different failure scenarios.
- **Text File Storage for Metadata:**  
  - Commit metadata (such as parent commit, timestamp, and message) is stored in text files within the repository structure.
- **Staging Mechanism and Unique Identifiers:**  
  - Uses `random` for generating unique commit IDs and implements a basic staging process similar to Git.
- **Graphical Commit History Representation:**  
  - Commit history is visualized using `matplotlib` and `networkx`, providing a clear representation of commit relationships.

## Summary
Wit-Project is an educational project that demonstrates how a basic version control system can be implemented in Python. It focuses on file system management, error handling, data persistence, and graphical visualization. This project is ideal for learning about version control principles and developing CLI-based tools.

