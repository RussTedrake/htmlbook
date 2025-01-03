#! /usr/bin/env python3
import os
import re

def find_pyproject_toml(start_path=None):
    if start_path is None:
        start_path = os.getcwd()
        
    pyproject_path = os.path.join(start_path, "pyproject.toml")
    if os.path.isfile(pyproject_path):
        return pyproject_path
        
    parent_dir = os.path.dirname(start_path)
    if parent_dir == start_path:  # Reached root directory
        raise AssertionError("could not find pyproject.toml")
        
    return find_pyproject_toml(parent_dir)

def get_project_name():
    """Extract project name from pyproject.toml file.
    
    Args:
        pyproject_path: Path to pyproject.toml file
        
    Returns:
        Project name as string
        
    Raises:
        AssertionError: If project name cannot be found
    """
    pyproject_path = find_pyproject_toml()
    with open(pyproject_path) as f:
        content = f.read()
        
    # Look for name = "something" or name = 'something'
    match = re.search(r'''name\s*=\s*["']([^"']+)["']''', content)
    if not match:
        raise AssertionError("could not find project name in pyproject.toml")
        
    return match.group(1)

if __name__ == "__main__":
    print(get_project_name())




