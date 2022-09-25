import typer
from rich import print
from .core import (
    create_remote_docker_client,
    RemoteDockerClient
)
from yaml import safe_load
from .config import PerryConfig

app = typer.Typer()

@app.command()
def test(
    ctx: typer.Context
):
    """Test new config"""
    print("hello Dav :)")

@app.command()
def create_key_pair(
    ctx: typer.Context
):
    """Create and upload a new keypair to AWS for SSH access"""
    client: RemoteDockerClient  = ctx.obj
    client.create_keypair()

@app.command()
def create(
    ctx: typer.Context
):
    """Provision a new ec2 instance to use as the remote agent"""
    client: RemoteDockerClient  = ctx.obj
    print(client.create_instance())
    client.use_remote_context()

@app.command()
def start(
    ctx: typer.Context
):
    """Start the remote agent instance"""
    client: RemoteDockerClient  = ctx.obj
    print(client.start_instance())
    client.use_remote_context()

@app.command()
def sync(
    ctx: typer.Context
):
    """Sync the given directories with the remote instance"""
    client: RemoteDockerClient  = ctx.obj
    client.sync()

@app.command()
def ssh(
    ctx: typer.Context
):
    """Connect to the remote agent via SSH"""
    client: RemoteDockerClient  = ctx.obj
    client.ssh_connect()

@app.command()
def stop(
    ctx: typer.Context
):
    """Stop the remote agent instance"""
    client: RemoteDockerClient  = ctx.obj
    print(client.stop_instance())
    client.use_default_context()

@app.command()
def delete(
    ctx: typer.Context
):
    """Delete the provisioned ec2 instance"""
    client: RemoteDockerClient  = ctx.obj
    print(client.delete_instance())
    client.use_default_context()

@app.command()
def tunnel(
    ctx: typer.Context
):
    """
    Create a SSH tunnel to the remote instance to connect
    with the docker agent and containers
    """
    client: RemoteDockerClient  = ctx.obj
    client.start_tunnel()

@app.callback()
def entry(
    ctx: typer.Context,
    config_path: str = typer.Option(
        "./perry_config.yml",
        help="Path of the perry config",
    )
):
    loaded_yaml = safe_load(open(config_path))
    config = PerryConfig.parse_obj(loaded_yaml)
    ctx.obj = create_remote_docker_client(config)

if __name__ == "__main__":
    app()