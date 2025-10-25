from pathlib import Path
from open_sandboxes.uv_config import PyprojectConfig
from open_sandboxes.ssh_connection import SSHConnection
from open_sandboxes.models import CodeOutput
from typing import Optional, Any


class Sandbox:
    def __init__(
        self,
        name: str,
        remote_connection: SSHConnection,
        config: Optional[PyprojectConfig] = None,
        pyproject_file_path: Optional[str] = None,
    ) -> None:
        """
        Initialize a Sandbox instance.

        Args:
            name (str): The name of the sandbox.
            remote_connection (SSHConnection): The SSH connection to the remote host.
            config (Optional[PyprojectConfig]): The configuration object for the pyproject.
                Provide either this or `pyproject_file_path`, not both.
            pyproject_file_path (Optional[str]): The file path to the pyproject configuration file.
                Provide either this or `config`, not both.

        Raises:
            ValueError: If neither or both `config` and `pyproject_file_path` are provided.
            ValueError: If the provided `pyproject_file_path` does not exist or is not a file.
        """
        if config is None and pyproject_file_path is None:
            raise ValueError(
                "You need to provide either a configuration or the path to a pyproject file"
            )
        elif config is not None and pyproject_file_path is not None:
            raise ValueError(
                "You can provide either a configuration or the path to a pyproject file, not both"
            )
        elif config is not None and pyproject_file_path is None:
            self.pyproject = config.to_str()
        elif config is None and pyproject_file_path is not None:
            if (
                not Path(pyproject_file_path).exists()
                or not Path(pyproject_file_path).is_file()
            ):
                raise ValueError(
                    "The provided path either does not exist or is not a file"
                )
            with open(pyproject_file_path, "r") as f:
                self.pyproject = f.read()
        self.name = name
        self.remote_connection = remote_connection

    @classmethod
    def from_connection_args(
        cls,
        name: str,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        passphrase: Optional[str] = None,
        key_file: Optional[str] = None,
        config: Optional[PyprojectConfig] = None,
        pyproject_file_path: Optional[str] = None,
    ) -> "Sandbox":
        """
        Create a Sandbox instance from SSH connection arguments.

        Args:
            name (str): The name of the sandbox.
            host (str): The SSH host address.
            port (int): The SSH port number.
            username (str): The SSH username.
            password (Optional[str]): The SSH password. Defaults to None.
            passphrase (Optional[str]): The passphrase for the SSH key. Defaults to None.
            key_file (Optional[str]): Path to the SSH private key file. Defaults to None.
            config (Optional[PyprojectConfig]): Optional configuration object. Defaults to None.
            pyproject_file_path (Optional[str]): Path to the pyproject file. Defaults to None.

        Returns:
            Sandbox: An instance of the Sandbox class initialized with the provided connection arguments.
        """
        conn = SSHConnection(
            host=host,
            port=port,
            username=username,
            password=password,
            passphrase=passphrase,
            key_file=key_file,
        )
        return cls(
            name=name,
            remote_connection=conn,
            config=config,
            pyproject_file_path=pyproject_file_path,
        )

    def _get_env_exports(self, environment: dict[str, Any]) -> str:
        exports = []
        for k, v in environment.items():
            exports.append(f"export {k}='{v}'")
        return " && ".join(exports)

    def run_code(
        self,
        code: str,
        timeout: Optional[float] = None,
        environment: Optional[dict[str, Any]] = None,
        cpus: Optional[float] = None,
        memory: Optional[int] = None,
        processes: Optional[int] = None,
        read_rate: Optional[str] = None,
        write_rate: Optional[str] = None,
    ) -> CodeOutput:
        """
        Executes the provided Python code in a remote Docker sandbox with configurable resource limits.

        Args:
            code (str): The Python code to execute.
            timeout (Optional[float]): Maximum time in seconds to allow for execution. Defaults to None.
            environment (Optional[dict[str, Any]]): Environment variables to set inside the container. Defaults to None.
            cpus (Optional[float]): Number of CPUs to allocate to the container. Defaults to 1 if not specified.
            memory (Optional[int]): Memory limit in megabytes for the container. Defaults to 512 MB if not specified.
            processes (Optional[int]): Maximum number of processes allowed in the container. Defaults to 100 if not specified.
            read_rate (Optional[str]): Maximum device read rate (e.g., "10mb"). Defaults to "10mb" if not specified.
            write_rate (Optional[str]): Maximum device write rate (e.g., "10mb"). Defaults to "10mb" if not specified.

        Returns:
            CodeOutput: A dictionary containing the standard output and error output from the code execution.

            ```
            {
                "output": str,  # Standard output from the executed code
                "error": str    # Standard error from the executed code
            }
            ```
        """
        cpu_limit = cpus or 1
        memory_limit = memory or 512
        processes_limit = processes or 100
        read_rate_limit = read_rate or "10mb"
        write_rate_limit = write_rate or "10mb"
        pyproject_escaped = self.pyproject.replace("'", "'\\''")
        code_escaped = code.replace("'", "'\\''")
        if environment:
            exports = self._get_env_exports(environment)
            command = f"""docker run --pids-limit {processes_limit} --cpus {cpu_limit} -m {memory_limit}m --device-read-bps=/dev/sda:{read_rate_limit} --device-write-bps=/dev/sda:{write_rate_limit} --rm ghcr.io/astral-sh/uv:alpine /bin/sh -c '
{exports} && \
mkdir -p /tmp/{self.name} && \
cat > /tmp/{self.name}/pyproject.toml << "EOF"
{pyproject_escaped}
EOF
cat > /tmp/{self.name}/script.py << "EOF"
{code_escaped}
EOF
cd /tmp/{self.name}/ && \
uv run script.py
'"""
        else:
            command = f"""docker run --pids-limit {processes_limit} --cpus {cpu_limit} -m {memory_limit}m --device-read-bps=/dev/sda:{read_rate_limit} --device-write-bps=/dev/sda:{write_rate_limit} --rm ghcr.io/astral-sh/uv:alpine /bin/sh -c '
mkdir -p /tmp/{self.name} && \
cat > /tmp/{self.name}/pyproject.toml << "EOF"
{pyproject_escaped}
EOF
cat > /tmp/{self.name}/script.py << "EOF"
{code_escaped}
EOF
cd /tmp/{self.name}/ && \
uv run script.py
'"""
        result = self.remote_connection.execute_command(command, timeout=timeout)
        return {"output": result["stdout"], "error": result["stderr"]}
