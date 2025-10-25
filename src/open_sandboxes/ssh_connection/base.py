import paramiko

from typing import Optional, cast
from open_sandboxes.models import ExecCommandResponse


class SSHConnection:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        passphrase: Optional[str] = None,
        key_file: Optional[str] = None,
    ) -> None:
        """
        Initialize a remote SSH connection.

        Args:
            host (str): The hostname or IP address of the SSH server.
            port (int): The port number to connect to on the SSH server.
            username (str): The username to authenticate as.
            password (Optional[str]): The password for authentication. Required if passphrase is not provided.
            passphrase (Optional[str]): The passphrase for the private key file. Required if password is not provided.
            key_file (Optional[str]): The path to the private key file. Required if passphrase is provided.

        Raises:
            ValueError: If neither password nor passphrase is provided.
            ValueError: If passphrase is provided without a key_file.
        """
        self.key_file: Optional[str] = None
        self.password: str = ""
        if password is None and passphrase is None:
            raise ValueError("You must provide one of password and passphrase")
        elif password is not None and passphrase is None:
            self.password = password
            self._is_passphrase = False
        else:
            if key_file is None:
                if password is not None:
                    self.password = password
                    self._is_passphrase = False
                else:
                    raise ValueError(
                        "If you provide a passhprase, you must also provide the file where the private key is stored"
                    )
            else:
                self.key_file = key_file
                self.password = cast(str, passphrase)
                self._is_passphrase = True
        self.host = host
        self.port = port
        self.username = username
        self._client = paramiko.SSHClient()
        self._is_connected = False

    def _connect(self) -> None:
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self._is_passphrase:
            self._client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                passphrase=self.password,
                key_filename=self.key_file,
            )
        else:
            self._client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
            )
        self._is_connected = True

    def execute_command(
        self,
        command: str,
        timeout: Optional[Optional[float]] = None,
    ) -> ExecCommandResponse:
        """
        Executes a command on the remote SSH server.

        Args:
            command (str): The command to execute on the remote server.
            timeout (Optional[float], optional): The maximum time in seconds to wait for command execution. Defaults to None.

        Returns:
            ExecCommandResponse: A dictionary containing 'stdout' and 'stderr' output from the executed command.

        Raises:
            Any exceptions raised by the underlying SSH client during connection or command execution.
        """
        if not self._is_connected:
            self._connect()
        _, stdout, stderr = self._client.exec_command(command=command, timeout=timeout)
        output = stdout.read().decode()
        error = stderr.read().decode()
        return {"stderr": error, "stdout": output}

    def _close(self) -> None:
        self._client.close()
