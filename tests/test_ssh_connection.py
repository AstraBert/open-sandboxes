import pytest

from typing import Any, Optional
from paramiko import SSHClient
from open_sandboxes.models import ExecCommandResponse
from open_sandboxes.ssh_connection import SSHConnection


class MockSSHConnection(SSHConnection):
    def _connect(self) -> None:
        self._is_connected = True
        return None

    def execute_command(
        self,
        command: str,
        timeout: Optional[float] = None,
        environment: Optional[dict[str, Any]] = None,
    ) -> ExecCommandResponse:
        if not self._is_connected:
            self._connect()
        if command.startswith("docker"):
            return {"stderr": "", "stdout": "Test code successfully executed!"}
        else:
            return {"stdout": "", "stderr": "Command not recognized"}


def test_ssh_connection_init() -> None:
    conn = SSHConnection(host="0.0.0.0", port=22, username="test", password="test")
    assert not conn._is_connected
    assert not conn._is_passphrase
    assert isinstance(conn._client, SSHClient)
    with pytest.raises(ValueError):
        SSHConnection(host="0.0.0.0", port=22, username="test")
    with pytest.raises(ValueError):
        SSHConnection(host="0.0.0.0", port=22, username="test", passphrase="test")
    conn1 = SSHConnection(
        host="0.0.0.0", port=22, username="test", passphrase="test", password="hello"
    )
    assert conn1.password == "hello"
    assert not conn1._is_passphrase
    conn2 = SSHConnection(
        host="0.0.0.0",
        port=22,
        username="test",
        passphrase="test",
        password="hello",
        key_file="/path/to/.ssh/key",
    )
    assert conn2.password == "test"
    assert conn2._is_passphrase


def test_ssh_connection_connect() -> None:
    conn = MockSSHConnection(host="0.0.0.0", port=22, username="test", password="test")
    conn._connect()
    assert conn._is_connected


def test_ssh_connection_exec() -> None:
    conn = MockSSHConnection(host="0.0.0.0", port=22, username="test", password="test")
    ret = conn.execute_command("docker ps -a")
    assert ret["stderr"] == "" and ret["stdout"] == "Test code successfully executed!"
    assert conn._is_connected
    ret = conn.execute_command("ls -la")
    assert ret["stderr"] == "Command not recognized" and ret["stdout"] == ""
