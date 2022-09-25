import os
import shlex
import subprocess
from getpass import getuser
from typing import Dict, List

from .config import PerryConfig
from .constants import (
    INSTANCE_USERNAME
)
from .providers import AWSInstanceProvider, InstanceProvider
from .util import logger


class RemoteDockerClient:
    def __init__(
        self,
        instance: InstanceProvider,
        local_port_forwards: Dict[str, Dict[str, str]],
        remote_port_forwards: Dict[str, Dict[str, str]],
        ssh_key_path: str,
        sync_dir: str,
        ignore_dirs: str,
        project_code: str,
    ):
        self.instance = instance
        self.local_port_forwards = local_port_forwards
        self.remote_port_forwards = remote_port_forwards
        self.ssh_key_path = ssh_key_path
        self.sync_dir = sync_dir
        self.ignore_dirs = ignore_dirs
        self.project_code = project_code

    @classmethod
    def from_config(cls, config: PerryConfig):
        instance = AWSInstanceProvider(
            username=INSTANCE_USERNAME,
            project_code=config.project_code,
            aws_region=config.aws_region,
            instance_service_name=config.instance_service_name,
            instance_type=config.instance_type,
            ssh_key_pair_name=config.key_pair_name,
            volume_size=config.volume_size,
        )

        return cls(
            instance=instance,
            local_port_forwards=config.local_port_forwards,
            remote_port_forwards=config.remote_port_forwards,
            ssh_key_path=config.non_null_key_path,
            sync_dir=config.expanded_sync_dir,
            ignore_dirs=config.ignore_dirs,
            project_code=config.project_code
        )

    def get_ip(self) -> str:
        logger.debug("Retrieving IP address of instance")
        return self.instance.get_ip()

    def start_instance(self):
        logger.info("Starting instance")
        return self.instance.start_instance()

    def stop_instance(self):
        logger.info("Stopping instance")
        return self.instance.stop_instance()

    def enable_termination_protection(self):
        logger.info("Enabling Termination protection")
        return self.instance.enable_termination_protection()

    def disable_termination_protection(self):
        logger.info("Disabling Termination protection")
        return self.instance.disable_termination_protection()

    def is_termination_protection_enabled(self) -> bool:
        return self.instance.is_termination_protection_enabled()

    def start_tunnel(self):

        ip = self.instance.get_ip()
        cmd_s = (
            "sudo ssh -v -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=no"
            " -o ServerAliveInterval=60 -N -T"
            f" -i {self.ssh_key_path} {self.instance.username}@{ip}"
        )

        target_sock = f"/var/run/{self.project_code}.sock"
        cmd_s += (
            f" -L {target_sock}:/var/run/docker.sock"
            " -o StreamLocalBindUnlink=yes"
            " -o PermitLocalCommand=yes"
            f" -o LocalCommand='sudo chown {getuser()} {target_sock}'"
        )

        for _name, port_mappings in self.local_port_forwards.items():
            for port_from, port_to in port_mappings.items():
                cmd_s += f" -L localhost:{port_from}:localhost:{port_to}"

        for _name, port_mappings in self.remote_port_forwards.items():
            for port_from, port_to in port_mappings.items():
                cmd_s += f" -R 0.0.0.0:{port_from}:localhost:{port_to}"

        logger.info("Starting tunnel")
        cmd = shlex.split(cmd_s)
        logger.debug("Running command: %s", cmd_s)

        logger.debug("Forwarding: ")
        logger.debug("Local: %s", self.local_port_forwards)
        logger.debug("Remote: %s", self.remote_port_forwards)
        subprocess.run(cmd, check=True)

    def create_instance(self):
        logger.info("Creating instance")
        return self.instance.create_instance(self.ssh_key_path)

    def delete_instance(self) -> Dict:
        logger.warning("Deleting instance")
        return self.instance.delete_instance()

    def ssh_connect(self, *, ssh_cmd: str = None, options: str = None):
        return self.instance.ssh_connect(
            ssh_key_path=self.ssh_key_path,
            ssh_cmd=ssh_cmd,
            options=options,
        )

    def ssh_run(self, *, ssh_cmd: str):
        return self.instance.ssh_run(
            ssh_key_path=self.ssh_key_path,
            ssh_cmd=ssh_cmd,
        )

    def create_keypair(self) -> Dict:
        return self.instance.create_keypair(self.ssh_key_path)

    def use_remote_context(self):
        logger.info(f"Switching docker context to {self.project_code}")

        subprocess.run(
            (
                f"docker context inspect {self.project_code} &>/dev/null || "
                "docker context create"
                f" --docker host=unix:///var/run/{self.project_code}.sock {self.project_code}"
            ),
            check=True,
            shell=True,
        )
        subprocess.run(
            f"docker context use {self.project_code} >/dev/null",
            check=True,
            shell=True,
        )

    def use_default_context(self):
        logger.info("Switching docker context to default")

        subprocess.run("docker context use default >/dev/null", check=True, shell=True)


    def _get_unison_cmd(
        self,
        *,
        ip: str,
        replica_path: str,
        ignore_dirs: List[str],
        force: bool = False,
        repeat_watch: bool = False,
    ) -> List[str]:
        cmd_s = (
            f"unison {replica_path}"
            f" 'ssh://{self.instance.username}@{ip}/{replica_path}'"
            f" -prefer {replica_path} -batch -sshargs '-i {self.ssh_key_path}'"
        )
        
        for ignore_dir in ignore_dirs:
            cmd_s += f" -ignore 'Name {{,.*,*,*/,.*/}}{ignore_dir}{{.*,*,*/,.*/}}'"

        if force:
            cmd_s += f" -force {replica_path}"
        if repeat_watch:
            cmd_s += " -repeat watch"

        return shlex.split(cmd_s.replace("\n", ""))

    def sync(self):
        ip = self.get_ip()

        logger.info("Ensuring remote directories exist")
        ssh_cmd_s = (
            f"sudo install -d -o {self.instance.username} -g {self.instance.username}"
        )
        ssh_cmd_s += f" -p {self.sync_dir}"
        
        self.ssh_run(ssh_cmd=ssh_cmd_s)

        logger.info("deleting any files owned by root (this messes with unison)")

        clean_cmd = (
            f"find {self.sync_dir} -user root -exec rm -fr {{}} \\\;"
        )
        self.ssh_run(ssh_cmd=clean_cmd)

        # First push the local replica's contents to remote
        logger.info("Pushing local files to remote server")

        logger.info(f"syncing self.sync_dir={self.sync_dir}")
        return 
        subprocess.run(
            self._get_unison_cmd(
                ip=ip,
                replica_path=self.sync_dir,
                ignore_dirs=self.ignore_dirs,
                force=True,
            ),
            check=True,
        )

        # Then watch for update
        logger.info("Watching local and remote filesystems for changes")
        watch_cmd = self._get_unison_cmd(
            ip=ip,
            replica_path=self.sync_dir,
            ignore_dirs=self.ignore_dirs,
            repeat_watch=True,
        )

        logger.debug("Running command: %s", watch_cmd)
        os.execvp(watch_cmd[0], watch_cmd)


def create_remote_docker_client(
    config: PerryConfig,
) -> RemoteDockerClient:
    return RemoteDockerClient.from_config(config)
