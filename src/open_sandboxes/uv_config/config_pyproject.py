from dataclasses import dataclass, field

from open_sandboxes.models import PyprojectDependency


@dataclass
class PyprojectConfig:
    """
    Represents the configuration for a Python project's `pyproject.toml` file.

    Attributes:
        dependencies (list[PyprojectDependency]):
            A list of dependencies required by the project, each represented as a PyprojectDependency.
        title (str):
            The name of the project. Defaults to "my-project".
        python_min_version (str):
            The minimum required Python version. Defaults to "3.13".
        python_max_version (str):
            The maximum supported Python version. Defaults to "4".

    Methods:
        to_str() -> str:
            Generates a string representation of the configuration in `pyproject.toml` format.
    """

    dependencies: list[PyprojectDependency]
    title: str = field(default="my-project")
    python_min_version: str = field(default="3.13")
    python_max_version: str = field(default="4")

    def to_str(self) -> str:
        deps = ""
        for dependency in self.dependencies:
            deps += f'    "{dependency["name"]}{dependency["version_constraints"]}",\n'
            deps = deps.strip(",\n")
        return f"""
[project]
name = "{self.title}"
version = "0.1.0"
description = "Add your description here"
requires-python = ">={self.python_min_version},<{self.python_max_version}"
dependencies = [
    {deps}
]
"""
