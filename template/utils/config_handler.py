from pathlib import Path
from typing import Dict, Any
import json
import shutil

class ConfigHandler:
    """Base class for handling configuration files"""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.config_dir = template_dir / 'config'

    def _create_directory(self, path: Path) -> None:
        """Create directory if it doesn't exist"""
        if not path.exists():
            path.mkdir(parents=True)

    def _copy_directory(self, src: Path, dst: Path) -> None:
        """Copy directory recursively"""
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def _copy_file(self, src: Path, dst: Path) -> None:
        """Copy single file"""
        if src.exists():
            shutil.copy2(src, dst)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file"""
        if not path.exists():
            return {}
        with open(path, 'r') as f:
            return json.load(f)

    def _save_json(self, data: Dict[str, Any], path: Path) -> None:
        """Save data to JSON file"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def _get_base_config(self) -> Dict[str, Any]:
        """Get base configuration structure"""
        return {
            "config_files": {
                "BasicConfig": {"active": True},
                "MailConfig": {"active": True},
                "UserConfig": {"active": True},
                "DebugConfig": {"active": True},
                "EditorConfig": {"active": True},
                "SkinConfig": {"active": True},
                "ParserFunctions": {"active": True},
                "CustomFunctions": {"active": False}
            },
            "extensions": {
                "composer": {},
                "download": {},
                "git": {}
            },
            "skins": {
                "git": {},
                "composer": {}
            }
        }
