from pathlib import Path
from open_sandboxes.uv_config import PyprojectConfig
from open_sandboxes.ssh_connection import SSHConnection
from open_sandboxes.models import CodeOutput
from typing import Optional, Any

class Sandbox:
    def __init__(self, name: str, remote_connection: SSHConnection, config: Optional[PyprojectConfig] = None, pyproject_file_path: Optional[str] = None) -> None:
        if config is None and pyproject_file_path is None:
            raise ValueError("You need to provide either a configuration or the path to a pyproject file")
        elif config is not None and pyproject_file_path is not None:
            raise ValueError("You can provide either a configuration or the path to a pyproject file, not both")
        elif config is not None and pyproject_file_path is None:
            self.pyproject = config.to_str()
        elif config is None and pyproject_file_path is not None:
            if not Path(pyproject_file_path).exists() or not Path(pyproject_file_path).is_file():
                raise ValueError("The provided path either does not exist or is not a file")
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
        conn = SSHConnection(host=host, port=port, username=username, password=password, passphrase=passphrase, key_file=key_file)
        return cls(name=name, remote_connection=conn, config=config, pyproject_file_path=pyproject_file_path)

    def run_code(self, code: str, timeout: Optional[float] = None, environment: Optional[dict[str, Any]] = None) -> CodeOutput:
        pyproject_escaped = self.pyproject.replace("'", "'\\''")
        code_escaped = code.replace("'", "'\\''")
        command = f"""docker run --rm ghcr.io/astral-sh/uv:alpine /bin/sh -c '
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
        result = self.remote_connection.execute_command(command, timeout=timeout, environment=environment)
        return {"output": result["stdout"], "error": result["stderr"]}

