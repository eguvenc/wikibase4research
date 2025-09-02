from pathlib import Path
from typing import Dict, List, Optional
import json
import shutil
from .config_handler import ConfigHandler
from .ui import UI
from jinja2 import Template

class ExtensionParser(ConfigHandler):
    """Handles MediaWiki extension configuration and management"""

    def __init__(self, template_dir: Path):
        super().__init__(template_dir)
        self.extensions_dir = template_dir / 'extensions'
        self.available_extensions = self._load_available_extensions()
        self.selected_extensions = {}
        self.selected_skins = {}
        self.ui = UI()

    def _load_available_extensions(self) -> Dict:
        """Load all available extensions from the extensions directory"""
        extensions = {}
        if not self.extensions_dir.exists():
            return extensions

        for ext_dir in self.extensions_dir.iterdir():
            if ext_dir.is_dir():
                manifest_path = ext_dir.joinpath('manifest.json')
                if manifest_path.exists():
                    manifest = self._load_json(manifest_path)
                    extensions[ext_dir.name] = manifest
        return extensions

    def _generate_extension_management_json(self) -> Dict:
        """Generate extensionManagement.json content"""
        config = self._get_base_config()

        # Process extensions with progress indication
        self.ui.display_info("Processing extension configurations...")
        for ext_name, ext_info in self.selected_extensions.items():
            # Extract the first key-value pair from the manifest
            install_type, ext_data = next(iter(ext_info.items()))
            if install_type in ["composer", "download", "git"]:
                for name, config_data in ext_data.items():
                    config["extensions"][install_type][name] = config_data
                    self.ui.display_info(f"Added {name} configuration")

        # Process skins (assuming they're stored similarly to extensions)
        if hasattr(self, 'selected_skins'):
            for skin_name, skin_info in self.selected_skins.items():
                install_type, skin_data = next(iter(skin_info.items()))
                if install_type in ["composer", "git"]:
                    for name, config_data in skin_data.items():
                        config["skins"][install_type][name] = config_data

        return config


    def _copy_extension_files(self, destination: Path) -> None:
        """Copy extension configuration files to destination"""
        self._create_directory(destination)

        for ext_name in self.selected_extensions.keys():
            src_dir = self.extensions_dir / ext_name
            dst_dir = destination / ext_name
            self._copy_directory(src_dir, dst_dir)

    def _generate_localsettings(self, destination: Path) -> None:
        """Generate LocalSettings.d directory with extension configs"""
        localsettings_dir = destination / 'LocalSettings.d'
        self._create_directory(localsettings_dir)

        # Copy base configuration files
        base_configs = [
            '00_BasicConfig.php',
            '01_MailConfig.php',
            '02_UserConfig.php',
            '03_DebugConfig.php',
            '04_EditorConfig.php',
            '100_SkinConfig.php',
            '10000_CustomFunctions.php'
        ]

        for config in base_configs:
            src = self.extensions_dir / '.MediawikiBaseConfiguration' / config
            dst = localsettings_dir / config
            self._copy_file(src, dst)

        # Generate extension-specific LocalSettings
        for i, ext_name in enumerate(self.selected_extensions.keys(), start=1030):
            config_name = f"{i}_{ext_name}.php"
            src = self.extensions_dir / ext_name / f"{ext_name}Config.php"
            dst = localsettings_dir / config_name
            self._copy_file(src, dst)

        self.save_extension_management_json(destination)

    def interactive_selection(self) -> None:
        """Interactive extension selection process with collection support"""
        self.ui.clear_screen()
        self.ui.display_header("Extension Configuration")

        # First, handle collection selection
        selected_collection = self._select_collection()
        self.selected_collection = selected_collection  # Save selected collection

        # Get pre-selected extensions from collection if one was chosen
        preselected_extensions = []
        if selected_collection:
            preselected_extensions = self._get_collection_extensions(selected_collection)
            self.ui.display_info("\nCollection includes these extensions:")
            self.ui.display_list(preselected_extensions)

            # Ask if user wants to modify the collection's extensions
            if not self.ui.confirm("\nWould you like to customize the extension selection?", default=False):
                self.selected_extensions = {ext: self.available_extensions[ext] for ext in preselected_extensions}
                self.ui.display_success("Using default collection extensions")
                return

        # Get available extensions
        available_exts = list(self.available_extensions.keys())

        # Get indices of preselected extensions
        preselected_indices = [
            i for i, ext in enumerate(available_exts)
            if ext in preselected_extensions
        ]

        self.ui.display_header("Extension Selection")
        self.ui.display_info("Available extensions:")
        self.ui.display_list(available_exts)

        # Show checkbox selection with preselected extensions
        choices = self.ui.prompt_checkbox(
            available_exts,
            "Choose extensions to install:",
            default_selected=preselected_indices
        )

        # Map selected extensions to their configurations
        self.selected_extensions = {ext: self.available_extensions[ext] for ext in choices}

        if self.selected_extensions:
            self.ui.display_success("Selected extensions:")
            self.ui.display_list(list(self.selected_extensions.keys()))
        else:
            self.ui.display_warning("No extensions were selected")


    def _load_collections(self) -> Dict:
        """Load collections from collections.json"""
        collections_file = self.extensions_dir / 'collections.json'
        if not collections_file.exists():
            return {}
        return self._load_json(collections_file).get('collections', {})

    def _select_collection(self) -> Optional[str]:
        """Prompt user to select a collection"""
        collections = self._load_collections()
        if not collections:
            self.ui.display_warning("No extension collections found")
            return None

        # Format collection choices for display
        collection_choices = ["No collection - manual selection"]
        collection_choices.extend([
            f"{data['name']}: {data['description']}"
            for data in collections.values()
        ])

        # Show collection selection
        self.ui.display_header("Extension Collections")
        self.ui.display_info("Choose a predefined collection or select extensions manually:")
        selected = self.ui.prompt_radio(collection_choices, "Select collection:")

        # If "No collection" was selected or nothing was selected
        if not selected or selected == "No collection":
            return None

        # Extract collection name from selection
        selected_name = selected.split(':')[0]

        # Find the collection key that matches the selected name
        for key, data in collections.items():
            if data['name'] == selected_name:
                return key

        return None

    def _get_collection_extensions(self, collection_key: str) -> List[str]:
        """Get list of extensions for a collection"""
        collections = self._load_collections()
        if collection_key in collections:
            return collections[collection_key].get('extensions', [])
        return []

    def get_collection_requirements(self, collection_key: str) -> set[str]:
        """Get required services for a collection"""
        collections = self._load_collections()
        if collection_key in collections:
            return set(collections[collection_key].get('requirements', {}).get('services', []))
        return set()

    def get_extension_info(self, extension_name: str) -> Optional[Dict]:
        """Get detailed information about a specific extension"""
        return self.available_extensions.get(extension_name)

    def get_selected_extensions(self) -> List[str]:
        """Get list of currently selected extensions"""
        return list(self.selected_extensions.keys())

    def _process_jinja_template(self, src: Path, dst: Path, env_data: Dict[str, any]) -> None:
        """Process a Jinja2 template file and write the result"""

        # Read the template
        with open(src, 'r') as f:
            template_content = f.read()

        # Create and render the template
        template = Template(template_content)
        rendered = template.render(**env_data)

        # Write the result
        with open(dst, 'w') as f:
            f.write(rendered)

    def get_selected_extensions_with_composer(self):
        composer_local_extensions = []

        for extension_name, extension_data in self.selected_extensions.items():
            # Check each installation method in the extension data
            for install_method in extension_data.values():
                # Check each configuration in the installation method
                for config in install_method.values():
                    if isinstance(config, dict) and config.get('composer.local') is True:
                        composer_local_extensions.append(extension_name)

        return composer_local_extensions

    def save_extension_management_json(self, destination: Path) -> None:
        """Save extensionManagement.json to the specified destination"""
        config = self._generate_extension_management_json()
        output_path = destination / 'extensionManagement.json'
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=4)

def main():
    parser = ExtensionParser(Path(__file__).parent.parent)
    parser.interactive_selection()
    parser._generate_localsettings(Path('output/config'))

if __name__ == "__main__":
    main()
