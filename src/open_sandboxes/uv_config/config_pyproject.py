from dataclasses import dataclass, field

from open_sandboxes.models import PyprojectDependency

@dataclass
class PyprojectConfig:
    dependencies: list[PyprojectDependency]
    title: str = field(default="my-project")
    python_min_version: str = field(default="3.13")
    python_max_version: str = field(default="4")

    def to_str(self) -> str:
        deps = ""
        for dependency in self.dependencies:
            deps+=f"\t\"{dependency['name']}{dependency['version_constraints']}\",\n" 
        return f"""
[project]
name = {self.title}
version = "0.1.0"
description = "Add your description here"
requires-python = ">={self.python_min_version},<{self.python_max_version}"
dependencies = [
    {deps}
]
"""



        