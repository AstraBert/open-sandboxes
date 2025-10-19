from typing import TypedDict

class PyprojectDependency(TypedDict):
    name: str
    version_constraints: str

class ExecCommandResponse(TypedDict):
    stdout: str
    stderr: str

class CodeOutput(TypedDict):
    output: str
    error: str

__all__ = ["PyprojectDependency", "ExecCommandResponse"]