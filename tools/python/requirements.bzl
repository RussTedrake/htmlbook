"""
Helper functions for automatic Python version selection.
Based on Drake's approach but simplified for pip repository selection.
"""

def requirement(package_name):
    """
    Returns the pip package reference for the given package name.
    
    This is a simplified version that uses a single pip repository.
    
    Args:
        package_name: The pip package name (e.g., "numpy", "drake")
        
    Returns:
        String reference to the pip package
    """
    return "@manipulation_pip//{}".format(package_name)