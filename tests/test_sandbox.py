import pytest

from unittest.mock import MagicMock
from open_sandboxes import Sandbox
from open_sandboxes.ssh_connection import SSHConnection
from open_sandboxes.uv_config import PyprojectConfig


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
