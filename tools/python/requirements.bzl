"""
Python package requirements with automatic version selection.

This system uses multiple pip.parse() calls with the same hub_name to support
Python 3.10, 3.12, and 3.13. The correct version is automatically selected
at runtime based on the configured Python version.

Supported Python versions:
- Python 3.10: For CI on Ubuntu Jammy (22.04)
- Python 3.12: For CI on Ubuntu Noble (24.04) 
- Python 3.13: For macOS development (Drake recommended)
"""

def requirement(package_name):
    """
    Returns the pip package reference for the given package name.
    
    Uses the single pip repository configured in MODULE.bazel.
    
    Args:
        package_name: The pip package name (e.g., "numpy", "drake")
        
    Returns:
        String reference to the pip package
    """
    return "@manipulation_pip//{}".format(package_name)

def all_requirements(package_names):
    """
    Returns a list of pip package references for multiple packages.
    
    Args:
        package_names: List of pip package names
        
    Returns:
        List of pip package references
    """
    return ["@manipulation_pip//{}".format(name) for name in package_names]