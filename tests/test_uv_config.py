import pytest

from open_sandboxes.uv_config import PyprojectConfig
from open_sandboxes.models import PyprojectDependency


@pytest.fixture()
def dependencies() -> list[PyprojectDependency]:
    return [
        {"name": "httpx", "version_constraints": ">=0.28.1,<1"},
        {"name": "typing-extensions", "version_constraints": "<5"},
    ]


def test_pyproject_config(dependencies: list[PyprojectDependency]) -> None:
    default_config = PyprojectConfig(dependencies=dependencies)
    default_config_str = default_config.to_str()
    with open("testfiles/default.pyproject.toml", "r") as f:
        default_content = f.read()
    assert default_content.replace(" ", "").replace(
        "\n", ""
    ) == default_config_str.replace(" ", "").replace("\n", "")
    custom_config = PyprojectConfig(
        dependencies=dependencies,
        title="http-server",
        python_min_version="3.10",
        python_max_version="3.13",
    )
    custom_config_str = custom_config.to_str()
    with open("testfiles/custom.pyproject.toml", "r") as f:
        custom_content = f.read()
    assert custom_content.replace(" ", "").replace(
        "\n", ""
    ) == custom_config_str.replace(" ", "").replace("\n", "")
