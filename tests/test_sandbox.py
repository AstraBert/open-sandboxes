import pytest

from typing import Optional, Any
from unittest.mock import MagicMock, patch
from open_sandboxes.sandbox import Sandbox
from open_sandboxes.ssh_connection import SSHConnection
from open_sandboxes.uv_config import PyprojectConfig
from open_sandboxes.models import CodeOutput


def test_sandbox_init() -> None:
    conn = SSHConnection(host="0.0.0.0", port=22, username="test", password="test")
    path = "testfiles/custom.pyproject.toml"
    sandbox = Sandbox(
        name="sandbox-1", remote_connection=conn, pyproject_file_path=path
    )
    assert sandbox.name == "sandbox-1"
    assert sandbox.remote_connection == conn
    with open(path, "r") as f:
        content = f.read()
    assert sandbox.pyproject == content
    config = PyprojectConfig(
        dependencies=[{"name": "typing-extensions", "version_constraints": "<5"}],
        title="test-project",
    )
    sandbox1 = Sandbox(name="sandbox-1", remote_connection=conn, config=config)
    assert sandbox1.pyproject == config.to_str()
    with pytest.raises(ValueError):
        Sandbox(name="sandbox-1", remote_connection=conn)
    with pytest.raises(ValueError):
        Sandbox(
            name="sandbox-1",
            config=config,
            remote_connection=conn,
            pyproject_file_path=path,
        )
    with pytest.raises(ValueError):
        Sandbox(
            name="sandbox-1",
            config=config,
            remote_connection=conn,
            pyproject_file_path="non-existing.toml",
        )


def test_sandbox_from_connection_args() -> None:
    path = "testfiles/custom.pyproject.toml"
    sandbox = Sandbox.from_connection_args(
        name="sandbox-1",
        username="test",
        password="test",
        host="0.0.0.0",
        port=22,
        pyproject_file_path=path,
    )
    assert isinstance(sandbox.remote_connection, SSHConnection)
    assert sandbox.remote_connection.username == "test"
    assert sandbox.remote_connection.password == "test"
    assert not sandbox.remote_connection._is_passphrase
    assert sandbox.remote_connection.host == "0.0.0.0"
    assert sandbox.remote_connection.port == 22
    with open(path, "r") as f:
        content = f.read()
    assert sandbox.pyproject == content


def test_sandbox_run_code() -> None:
    conn = SSHConnection(host="0.0.0.0", port=22, username="test", password="test")
    path = "testfiles/custom.pyproject.toml"
    sandbox = MagicMock()
    sandbox.remote_connection = conn
    with open(path, "r") as f:
        content = f.read()
    sandbox.pyproject = content
    sandbox.name = "sandbox-1"
    sandbox.run_code.return_value = {"output": "hello world!", "error": ""}
    res = sandbox.run_code("print('hello world!')")
    assert res["output"] == "hello world!"
    assert res["error"] == ""


def _get_env_exports(environment: dict[str, Any]) -> str:
    exports = []
    for k, v in environment.items():
        exports.append(f"export {k}='{v}'")
    return " && ".join(exports)


def mock_run_code(
    code: str,
    timeout: Optional[float] = None,
    environment: Optional[dict[str, Any]] = None,
    cpus: Optional[float] = None,
    memory: Optional[int] = None,
    processes: Optional[int] = None,
    read_rate: Optional[str] = None,
    write_rate: Optional[str] = None,
) -> CodeOutput:
    cpu_limit = cpus or 1
    memory_limit = memory or 512
    processes_limit = processes or 100
    read_rate_limit = read_rate or "10mb"
    write_rate_limit = write_rate or "10mb"
    pyproject_escaped = "hello"
    code_escaped = code.replace("'", "'\\''")
    if environment:
        exports = _get_env_exports(environment)
        command = f"""docker run --pids-limit {processes_limit} --cpus {cpu_limit} -m {memory_limit}m --device-read-bps=/dev/sda:{read_rate_limit} --device-write-bps=/dev/sda:{write_rate_limit} --rm ghcr.io/astral-sh/uv:alpine /bin/sh -c '
{exports} && \
mkdir -p /tmp/hello && \
cat > /tmp/hello/pyproject.toml << "EOF"
{pyproject_escaped}
EOF
cat > /tmp/hello/script.py << "EOF"
{code_escaped}
EOF
cd /tmp/hello/ && \
uv run script.py
'"""
    else:
        command = f"""docker run --pids-limit {processes_limit} --cpus {cpu_limit} -m {memory_limit}m --device-read-bps=/dev/sda:{read_rate_limit} --device-write-bps=/dev/sda:{write_rate_limit} --rm ghcr.io/astral-sh/uv:alpine /bin/sh -c '
mkdir -p /tmp/hello && \
cat > /tmp/hello/pyproject.toml << "EOF"
{pyproject_escaped}
EOF
cat > /tmp/hello/script.py << "EOF"
{code_escaped}
EOF
cd /tmp/hello/ && \
uv run script.py
'"""
    return {"output": command, "error": ""}


@patch("open_sandboxes.sandbox.Sandbox.run_code", new_callable=MagicMock)
def test_sandbox_run_code_options(mock: MagicMock) -> None:
    mock.side_effect = mock_run_code
    path = "testfiles/custom.pyproject.toml"
    sandbox = Sandbox.from_connection_args(
        name="sandbox-1",
        username="test",
        password="test",
        host="0.0.0.0",
        port=22,
        pyproject_file_path=path,
    )
    result = sandbox.run_code(
        "print('hello world!')",
        environment={"OPENAI_API_KEY": "test-key", "PYTHONBUFFERED": "1"},
        cpus=1.5,
        memory=100,
        processes=10,
        read_rate="1mb",
        write_rate="2mb",
    )
    assert (
        "export OPENAI_API_KEY='test-key' && export PYTHONBUFFERED='1'"
        in result["output"]
    )
    assert (
        "docker run --pids-limit 10 --cpus 1.5 -m 100m --device-read-bps=/dev/sda:1mb --device-write-bps=/dev/sda:2mb"
        in result["output"]
    )
    result = sandbox.run_code("print('hello world!')")
    assert "export" not in result["output"]
    assert (
        "docker run --pids-limit 100 --cpus 1 -m 512m --device-read-bps=/dev/sda:10mb --device-write-bps=/dev/sda:10mb"
        in result["output"]
    )
