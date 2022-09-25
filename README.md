## Perry The Docker Agent
### Your cool remote docker agent in the cloud ⛄️

[![PyPI version](https://badge.fury.io/py/perry-the-docker-agent.svg)](https://badge.fury.io/py/perry-the-docker-agent)
![Python versions](https://img.shields.io/pypi/pyversions/perry-the-docker-agent.svg?style=flat-square&label=Python%20Versions)

Based on [remote-docker-aws](https://github.com/lime-green/remote-docker-aws) 🙏🏾

Use docker to develop services, but without the overhead of running docker on your machine! This is a development tool that you should use if your machine is low performance, or if you are running many docker services.

### Why is this useful?

Frees up your local machine for useful tasks
such as running your code editor, browser, and email, leaving running Docker to a dedicated server instance.
The result is that your local machine functions faster, uses up less disk space, and consumes less power.
MacOS users will also see noticeable speed improvements since Docker on Linux (which is
what the remote hosts runs) is much more performant.

The downsides:
- SSH tunnel communication is slower than local communication. However using an AWS region with low ping makes the latency unnoticeable. Find the region fastest for you using [this site](https://www.cloudping.info/)
- Some more setup required to get everything configured properly and running (tunneling ports, syncing file changes)
- Running the ec2 instance incurs an additional cost over running locally, although a t3.medium instance in Canada only costs just under 5 cents/hour

How it works: two processes are run, a sync and a tunnel process. 
- The sync process keeps local and remote files in sync so that the docker process run remotely can use docker volumes transparently
- The tunnel process forwards ports needed so your local system can communicate with docker, plus additional ports as required, such as port 443 for browser communication

## Setup
1. First login to your AWS account and [create access keys to access AWS through the CLI](https://docs.aws.amazon.com/powershell/latest/userguide/pstools-appendix-sign-up.html)

    You will need the following IAM policies:
    - AmazonEC2FullAccess
    - AWSCloudFormationFullAccess

    And now in your terminal:

    ```bash
    # Replace dav with your name
    # You will need to setup an AWS account if you don't have one
    # and create access key credentials

    aws configure --profile dav
    export AWS_PROFILE=dav
    ```

1. Install pre-requisites

   Have [Homebrew](https://brew.sh/) (Available on both macOS and Linux now!)

   Have [pipx](https://github.com/pipxproject/pipx)

    ```bash
   pip install perry-the-docker-agent
   # or.... if part of a project
   poetry add perry-the-docker-agent

   # Install unison sync utility
   brew install unison

   # Install file-watcher driver for unison
   # On MacOS:
   brew install autozimu/homebrew-formulas/unison-fsmonitor

   # Or, on Linux since the above formula doesn't work:
   brew install eugenmayer/dockersync/unox
    ```

1. Generate and upload a keypair to AWS

    ```bash
   perry create-keypair
    ```

1. Create the ec2 instance

    ```bash
   perry create
    ```

## Daily Running

1. Start the remote-docker ec2 instance
    ```bash
    perry start
    ```
   This will automatically switch the docker context for you. If you want to switch
   back to the default agent run `docker context use default`

1. In one terminal start the tunnel so that the ports you need to connect to are exposed
    ```bash
    perry tunnel
    ```

1. In another terminal sync file changes to the remote instance:
    ```bash
    perry sync
    ```

1. Develop and code! All services should be accessible and usable as usual (eg: `docker ps`, `docker-compose up`, etc.)
as long as you are running `perry tunnel` and are forwarding the ports you need

1. When you're done for the day don't forget to stop the instance to save money:
    ```bash
    perry stop
    ```

## Config File
Looks for a config file at the path `./perry_config.yml` by default,
which can be overriden by passing `--config-path`. 

An example `perry_config.yml` file:
```yaml
aws_region: af-south-1
instance_type: t3.large
volume_size: 100
sync_dir: ./
project_id: "ranger"
ignore_dirs:
  - .venv
  - .git
  - node_modules
  - __pycache__
remote_port_forwards:
  local-webpack-app:
    "8080": "8080"
local_port_forwards:
  user-api:
    "2020": "2020"
  blog-api:
    "3030": "3030"
```

```bash
 Usage: perry [OPTIONS] COMMAND [ARGS]...                                                  
                                                                                           
╭─ Options ───────────────────────────────────────────────────────────────────────────────╮
│ --config-path               TEXT  Path of the perry config                              │
│                                   [default: ./perry_config.yml]                         │
│ --install-completion              Install completion for the current shell.             │
│ --show-completion                 Show completion for the current shell, to copy it or  │
│                                   customize the installation.                           │
│ --help                            Show this message and exit.                           │
╰─────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────╮
│ create           Provision a new ec2 instance to use as the remote agent                │
│ create-key-pair  Create and upload a new keypair to AWS for SSH access                  │
│ delete           Delete the provisioned ec2 instance                                    │
│ ssh              Connect to the remote agent via SSH                                    │
│ start            Start the remote agent instance                                        │
│ stop             Stop the remote agent instance                                         │
│ sync             Sync the given directories with the remote instance                    │
│ test             Test new config                                                        │
│ tunnel           Create a SSH tunnel to the remote instance to connect with the docker  │
│                  agent and containers                                                   │
╰─────────────────────────────────────────────────────────────────────────────────────────╯
```

The current configurable values can be seen in [config.py](perry/config.py)

#### `aws_region` (takes precedence over `AWS_REGION` and `.aws/config`)
- The region to create the instance in

#### `instance_type`
- Type of ec2 instance, defaults to: `t3.medium`

#### `project_id`
  - defaults to `None`
  - Used to uniquely identify the instance, this is useful if multiple remote-docker agents
  will be created in the same AWS account

#### `key_path`
  - defaults to: `~/.ssh/id_rsa_perry_{{project_id}}`

#### `local_port_forwards`
  - defaults to: `{}`
  - Object containing label -> port mapping objects for opening the ports on the remote host.
    A mapping of `"remote_port_forwards": {"my_app": {"80": "8080"}}` will open port 80 on your local machine
    and point it to port 8080 of the remote-docker instance (which ostensibly a container is listening on).
    The name doesn't do anything except help legibility.

#### `remote_port_forwards`
  - defaults to: `{}`
  - Similar to `local_port_forwards` except will open the port on the remote instance.

    This is useful to have frontend webpack apps accessible on the remote host

#### `ignore_dirs`
  - defaults to: `[]`
  - list of directories to ignore

#### `sync_dir`
 - directory to sync, will usually be the root fo the project

#### `volume_size`
 - defaults to: `30` (GB)
 - Size of the ec2 volume.

## Cost
A t3.medium instance on ca-central-1 currently costs $0.046 /hour. [See current prices](https://aws.amazon.com/ec2/pricing/on-demand/)

Nothing else used should incur any cost with reasonable usage

## Notes
- See `perry --help` for more information on the commands available
- The unison version running on the server and running locally have to
match. If one of them updates to a newer version, you should update the other.

## Perry improvements on [remote-docker-aws](https://github.com/lime-green/remote-docker-aws)
- Perry is configured to the project by a local `perry_config.yml`
- Perry uses [poetry](https://github.com/python-poetry/poetry), [pydantic](https://github.com/pydantic/pydantic) and [typer](https://github.com/tiangolo/typer)
- Perry enables swap accounting on the remote ec2 instance which allows docker-compose resource limits
- Perry uses a simpler method to sync and ignore directories.