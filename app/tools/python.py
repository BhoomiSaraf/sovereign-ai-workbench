from app.security.sandbox import DockerSandbox

# Attempt to load LangChain's @tool decorator if available, 
# otherwise use a passthrough to maintain compatibility.
try:
    from langchain_core.tools import tool
except ImportError:
    def tool(func):
        return func

# Singleton instance of the sandbox
_sandbox = DockerSandbox()

@tool
def python_repl(code: str) -> str:
    """
    Use this tool to execute Python code to perform math, calculations, or data manipulation. 
    Input must be a valid Python script.
    
    The code runs in a secure, air-gapped Docker sandbox without network access.
    To see the output of your operations, make sure to use print() statements in your code.
    If the code fails, an error trace will be returned for you to analyze and self-correct.
    """
    return _sandbox.execute_code(code)

# For compatibility with the current ToolRegistry
def execute_python(code: str) -> str:
    return python_repl(code)
