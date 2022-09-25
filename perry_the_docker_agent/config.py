import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

KEY_PAIR_NAME = "perry-keypair"
INSTANCE_SERVICE_NAME = "perry-ec2-agent"
SCEPTRE_PROJECT_CODE = "perry"

class PerryConfig(BaseModel):
    aws_region: str = "us-east-1"
    instance_type: str = "t3.medium"
    project_id: Optional[str]
    key_path: Optional[str]
    volume_size: int = 30
    ignore_dirs: List[str] = []
    local_port_forwards: Dict[str,Dict[str,str]] = {}
    remote_port_forwards: Dict[str,Dict[str,str]] = {}
    sync_dir: Path

    @property
    def instance_service_name(self) -> str:
        if self.project_id is not None:
            return f"{self.project_id}-{INSTANCE_SERVICE_NAME}"
        else:
            return INSTANCE_SERVICE_NAME

    @property
    def key_pair_name(self) -> str:
        if self.project_id is not None:
            return f"{self.project_id}-{KEY_PAIR_NAME}"
        else:
            return KEY_PAIR_NAME
    
    @property
    def non_null_key_path(self) -> str:
        if self.key_path is not None:
            return os.path.expanduser(self.key_path)
        else:
            under_score_project_code = self.project_code.replace("-","_")
            return os.path.expanduser(f"~/.ssh/id_rsa_{under_score_project_code}")

    @property
    def project_code(self) -> str:
        if self.project_id is not None:
            return f"{self.project_id}-{SCEPTRE_PROJECT_CODE}"
        else:
            return SCEPTRE_PROJECT_CODE
    
    @property
    def expanded_sync_dir(self) -> str:
        return os.path.expanduser(self.sync_dir.absolute())