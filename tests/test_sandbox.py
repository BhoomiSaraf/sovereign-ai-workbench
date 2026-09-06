import pytest
from app.tools.python import python_repl

def test_safe_code_execution():
    """
    Test 1: Run a simple Python script to ensure the sandbox 
    can execute code and return stdout correctly.
    """
    code = "import math\nprint(math.sqrt(144))"
    result = python_repl.invoke({"code": code})
    
    # We expect the output to be "12.0"
    assert "12.0" in result
    assert "Error" not in result

def test_malicious_network_code():
    """
    Test 2: Run a Python script attempting to access the internet.
    This must fail because the sandbox has network_disabled=True.
    """
    code = (
        "import urllib.request\n"
        "try:\n"
        "    response = urllib.request.urlopen('http://google.com', timeout=3)\n"
        "    print('Success')\n"
        "except Exception as e:\n"
        "    print(f'Failed: {type(e).__name__}')\n"
    )
    
    result = python_repl.invoke({"code": code})
    
    # We expect a failure (URLError/Temporary failure in name resolution)
    assert "Success" not in result
    assert "Failed: URLError" in result or "NameResolutionError" in result
