# open-sandboxes

`open-sandboxes` is an open-source, python-native and self-hosted-first alternative implementation of [Cloudflare Sandbox SDK](https://developers.cloudflare.com/sandbox/).

The only pre-requisite for running `open-sandboxes` is to have a cloud environment with Docker installed: whenever you want to execute python code remotely, you will simply leverage a `Sandbox` object which will create an ephemeral Docker container (based on `ghcr.io/astral-sh/uv:alpine`) on your remote machine, on which all the dependencies will be installed and the code will run.

## Installation

You can install `open-sandboxes` via pip:

```bash
pip install open-sandboxes
```

Or you can build it from source code:

```bash
git clone https://github.com/AstraBert/open-sandboxes
cd open-sandboxes
pip install [-e] . # use the -e option for editable installations
```

## Usage

To create a Sandbox instance, you need an SSH remote connection and a `pyproject.toml` file with all your dependencies listed. This can be provided:

1. With the path to the `pyproject.toml` file and a `SSHConnection` object:

```python
from open_sandboxes import Sandbox
from open_sandboxes.ssh_connection import SSHConnection

conn = SSHConnection(
    host="your-host.com",
    username="user",
    password="my-password",  # you can also use a passphrase with a private key file
    port=22,
)
sandbox = Sandbox(
    name="sandbox-1",
    remote_connection=conn,
    pyproject_file_path="pyproject.toml",
)
```

2. With a `PyprojectConfig` instance:

```python
from open_sandboxes import Sandbox
from open_sandboxes.ssh_connection import SSHConnection
from open_sandboxes.uv_config import PyprojectConfig

conn = SSHConnection(
    host="your-host.com",
    username="user",
    password="my-password",  # you can also use a passphrase with a private key file
    port=22,
)
config = PyprojectConfig(
    dependencies=[{"name": "httpx", "version_constraints": "<1"}],
    title="http-server",
    min_python_version="3.10",  # included (>=3.10)
    max_python_version="3.13",  # excluded (<3.13)
)
sandbox = Sandbox(name="sandbox-1", remote_connection=conn, config=config)
```

3. Using the `from_connection_args` class method:

```python
sandbox = Sandbox.from_connection_args(
    name="sandbox-1",
    username="user",
    passphrase="secret-passhprase",
    key_file=".ssh/key_file",
    host="your-host.com",
    port=22,
    pyproject_file_path="pyproject.toml",
)
```

Once you created a Sandbox instance, use the `run_code` method to run whatever code you want:

```python
code = """
import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        res = await client.get("https://uselessfacts.jsph.pl/api/v2/facts/random")
        res.raise_for_status()
        return res.json().get("text", "no text")

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"A random fact is: {result}")
"""

res = sandbox.run_code(code=code)
print("Code output:", res["output"])
print("Captured stderr logs:", res["error"])
```

You can configure `run_code` to:

- Export specific environment variables (passing a dictionary under the `environment` parameter)
- Enforce resource consumption limits to CPU, memory, number of processes and read/write rates.

## Contributing

Contributions are always welcome! Please read the [contributing guide](./CONTRIBUTING.md) to get to know more about the contribution process.

## License

This project is provided under an [MIT License](./LICENSE)
