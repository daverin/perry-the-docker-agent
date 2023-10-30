import os
from pathlib import Path
from typing import Dict, List, Optional
import os

from pydantic import BaseModel
import platform

KEY_PAIR_NAME = "perry-keypair"
INSTANCE_SERVICE_NAME = "perry-ec2-agent"
SCEPTRE_PROJECT_CODE = "perry"


class PerryConfig(BaseModel):
    # --- aws properties
    aws_region: str = "us-east-1"
    credentials_profile_name: str = "default"

    # --- naming
    project_id: str = "new-project"

    # --- networking
    bind_address: str = "localhost"

    # --- ssh
    key_path: Optional[str]

    # -- labeling
    env_label: Optional[str]

    env_label_suffix: str = "s"
    separator: str = "-"

    # --- unison properties
    ignore_dirs: List[str] = []
    local_port_forwards: Dict[str, Dict[str, str]] = {}
    remote_port_forwards: Dict[str, Dict[str, str]] = {}
    sync_paths: List[Path]

    # --- instance properties
    instance_type: str = "t3.medium"
    volume_size: int = 30
    instance_ami: Optional[str]
    instance_username = "ubuntu"
    bootstrap_command = r"""
        set -x
        && sudo sysctl -w net.core.somaxconn=4096
        && sudo echo GRUB_CMDLINE_LINUX=\\"\"cdgroup_enable=memory swapaccount=1\\"\" | sudo tee -a /etc/default/grub.d/50-cloudimg-settings.cfg
        && sudo update-grub
        && sudo rm /var/lib/dpkg/lock
        && sudo dpkg --configure -a
        && sudo apt-get -y update
        && sudo apt-get -y install docker.io || true
        && sudo usermod -aG docker ubuntu  || true
        && sudo systemctl daemon-reload || true
        && sudo systemctl restart docker.service || true
        && sudo systemctl enable docker.service || true
        && "sudo sed -i -e '/GatewayPorts/ s/^.*$/GatewayPorts yes/' '/etc/ssh/sshd_config'"
        && sudo service sshd restart
        && wget -qO- https://github.com/bcpierce00/unison/releases/download/v2.52.1/unison-v2.52.1+ocaml-4.01.0+x86_64.linux.tar.gz | tar -xvz
        && sudo mv bin/* /usr/local/bin/
        && sudo reboot
    """
    # Looked up via https://cloud-images.ubuntu.com/locator/ec2/
    # With filters:
    # Version: 18.04 LTS
    # Instance Type: hvm:ebs-ssd
    # Release: 20200626
    aws_region_to_ubuntu_ami_mapping = {
        "us-west-2": "ami-053bc2e89490c5ab7",
        "us-west-1": "ami-0d705db840ec5f0c5",
        "us-east-2": "ami-0a63f96e85105c6d3",
        "us-east-1": "ami-0ac80df6eff0e70b5",
        "sa-east-1": "ami-0faf2c48fc9c8f966",
        "me-south-1": "ami-0ca656ad4cf917e1f",
        "eu-west-3": "ami-0e11cbb34015ff725",
        "eu-west-2": "ami-00f6a0c18edb19300",
        "eu-west-1": "ami-089cc16f7f08c4457",
        "eu-south-1": "ami-08bb6fa4a2d8676d4",
        "eu-north-1": "ami-0f920d75f0ce2c4bb",
        "eu-central-1": "ami-0d359437d1756caa8",
        "ca-central-1": "ami-065ba2b6b298ed80f",
        "ap-southeast-2": "ami-0bc49f9283d686bab",
        "ap-southeast-1": "ami-063e3af9d2cc7fe94",
        "ap-south-1": "ami-02d55cb47e83a99a0",
        "ap-northeast-3": "ami-056ee91a6ed694f5d",
        "ap-northeast-2": "ami-0d777f54156eae7d9",
        "ap-northeast-1": "ami-0cfa3caed4b487e77",
        "ap-east-1": "ami-c42464b5",
        "af-south-1": "ami-079652134906bcbad",
    }

    def _prefix(self, value: str) -> str:
        value = f"{self.project_id}{self.separator}{value}"

        env_label = os.environ.get(self.system_env_label)
        value = f"{env_label}{self.env_label_suffix}{self.separator}{value}"
        return value

    @property
    def instance_service_name(self) -> str:
        return self._prefix(INSTANCE_SERVICE_NAME)

    @property
    def key_pair_name(self) -> str:
        return self._prefix(KEY_PAIR_NAME)

    @property
    def non_null_key_path(self) -> str:
        if self.key_path is not None:
            return os.path.expanduser(self.key_path)
        else:
            under_score_project_code = self.project_code.replace("-", "_")
            return os.path.expanduser(f"~/.ssh/id_rsa_{under_score_project_code}")

    @property
    def project_code(self) -> str:
        return self._prefix(SCEPTRE_PROJECT_CODE)

    @property
    def expanded_sync_dir(self) -> str:
        return os.path.expanduser("~")

    @property
    def expanded_sync_paths(self) -> List[str]:
        return [
            str(Path(os.path.expanduser(f)).absolute()).split(
                self.expanded_sync_dir + os.sep
            )[1]
            for f in self.sync_paths
        ]

    @property
    def system_env_label(self) -> str:
        if self.env_label is not None:
            return self.env_label
        else:
            if platform.system() == "Windows":
                return os.environ.get("USERNAME")
            else:
                return os.environ.get("USER")
