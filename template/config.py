from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import socket
import threading
import time
import sys
from utils.service_parser import ServiceParser
from utils.ui import UI
from utils.env_parser import EnvParser
from utils.extension_parser import ExtensionParser
from utils.template_processor import TemplateProcessor

class ConfigurationManager:
    def __init__(self, template_dir: Path):
        self.project_name = "Default"
        self.template_dir = template_dir
        self.ui = UI()
        self.env_parser = EnvParser(template_dir)
        self.ext_parser = ExtensionParser(template_dir)
        self.service_parser = ServiceParser(template_dir.parent)
        self.env_data: Dict[str, Dict[str, Any]] = {}
        self.extension_changes: List[str] = []
        self.service_changes: List[str] = []
        self.output_dir: Optional[Path] = None
        self.template_processor = TemplateProcessor(template_dir)

    def _animate_loading(self, stop_event):
        """Display an animation while waiting for socket resolution."""
        stop_event, live = self.ui.start_loading_animation("Checking hosts entry...")
        return stop_event, live

    def _check_hosts_entry(self, domain: str) -> bool:
        """Check if domain exists in /etc/hosts file."""
        stop_event = threading.Event()
        stop_event, live = self._animate_loading(stop_event)

        try:
            result = socket.gethostbyname(domain) == "127.0.0.1"
        except socket.gaierror:
            result = False
        finally:
            self.ui.stop_loading_animation(stop_event, live)

        return result

    def _get_service_url(self, subdomain: Optional[str] = None) -> str:
        """Generate service URL based on environment settings."""
        scheme = self.env_data['Server Settings']['W4R_SCHEME']['value']
        server = self.env_data['Server Settings']['W4R_SERVER_NAME']['value']
        port = self.env_data['ReverseProxy Settings']['W4R_REVERSEPROXY_PORT']['value']

        # Only include port if it's non-standard for the scheme
        base_url = f"{scheme}://{server}"
        if subdomain:
            base_url = f"{scheme}://{subdomain}.{server}"

        if (scheme == "http" and port != "80") or (scheme == "https" and port != "443"):
            return f"{base_url}:{port}"
        return base_url

    def _get_enabled_services_summary(self) -> List[str]:
        """Generate summary of enabled services."""
        summary = []
        enabled_services = set(
            self.env_data['INSTANCE Settings']['W4R_COMPOSER_SERVICE_INCLUDE']['value'].split(',')
        )

        service_configs = {
            'wdqs': ('Query Service', 'query'),
            'openrefine': ('OpenRefine Reconciliation', 'reconcile'),
            'kompakkt': ('Kompakkt', 'kompakkt'),
            'elasticsearch': ('Elasticsearch', None),
            'wbjobrunner': ('Job Runner', None)
        }

        for service, (name, subdomain) in service_configs.items():
            if service in enabled_services:
                if subdomain:
                    summary.append(f"    {name}: {self._get_service_url(subdomain)}")
                else:
                    summary.append(f"    {name}: Enabled")

        return summary

    def generate_summary(self) -> str:
        """Generate a comprehensive configuration summary."""
        if not self.env_data:
            return "No configuration changes to display."

        summary = ["\nDeployment Overview:"]

        # Main Wiki Information
        main_wiki = [
            "\n  Main Wiki:",
            f"    URL: {self._get_service_url()}",
            f"    Name: {self.env_data['MediaWiki Settings']['W4R_MW_WIKI_NAME']['value']}",
            f"    Admin Username: {self.env_data['MediaWiki Settings']['W4R_MW_ADMIN_USER']['value']}"
        ]
        summary.extend(main_wiki)

        # Server Configuration
        # Server Configuration
        server_config = [
            "\n  Server Configuration:",
            f"    Installation Directory: {str(self.output_dir)}"
        ]

        summary.extend(server_config)

        # Enabled Services
        enabled_services = self._get_enabled_services_summary()
        if enabled_services:
            summary.append("\n  Enabled Services:")
            summary.extend(enabled_services)

        if self.output_dir:
            summary.append(f"\nAll files will be saved to: {self.output_dir}")

        return "\n".join(summary)

    def generate_future_steps(self) -> str:
        """Generate instructions for next steps after configuration."""
        steps = [
            "\nNext Steps:",
            "1. Start the services by running:",
            f"   ./wiki.sh wikiProjects/{self.project_name} setup",
            "\n2. Wait for all services to initialize (this may take several minutes)",
            f"\n3. Access your Wikibase instance at: {self._get_service_url()}",
            "\n4. Please read the README file for detailed information about the system"
        ]

        # Add admin credentials reminder
        admin_user = self.env_data['MediaWiki Settings']['W4R_MW_ADMIN_USER']['value']
        admin_pass = self.env_data['MediaWiki Settings']['W4R_MW_ADMIN_PASS']['value']
        steps.extend([
            "\n5. Log in with your admin credentials:",
            f"   Username: {admin_user}",
            f"   Password: {admin_pass}"
        ])

        # Add information about enabled services
        enabled_services = set(
            self.env_data['INSTANCE Settings']['W4R_COMPOSER_SERVICE_INCLUDE']['value'].split(',')
        )

        if 'wdqs' in enabled_services:
            steps.extend([
                "\n6. Query Service:",
                f"   Access the SPARQL endpoint at: {self._get_service_url('query')}"
            ])

        if 'openrefine' in enabled_services:
            steps.extend([
                "\n7. OpenRefine Reconciliation:",
                f"   Configure OpenRefine to use: {self._get_service_url('reconcile')}"
            ])

        steps.extend([
            "\nNote: Initial startup may take several minutes as Docker images are pulled",
            "      and services are initialized. Please be patient."
        ])

        return "\n".join(steps)


    def collect_extension_changes(self) -> None:
        """Configure extensions and collect changes."""
        self.ui.display_header("Extension Configuration")
        self.ext_parser.interactive_selection()
        self.extension_changes = self.ext_parser.get_selected_extensions()

        # Determine required services from collection
        required_services = set()
        if hasattr(self.ext_parser, 'selected_collection') and self.ext_parser.selected_collection:
            required_services = self.ext_parser.get_collection_requirements(
                self.ext_parser.selected_collection
            )

        # Configure services
        self.ui.display_header("\nService Configuration")
        self.service_parser.select_services(required_services)
        self.service_changes = sorted(self.service_parser.get_selected_services())

    def collect_environment_changes(self) -> None:
        """Configure environment and collect changes."""
        template_file = self.template_dir / '.env.template'
        if not template_file.exists():
            self.ui.display_error("No .env.template file found in current directory")
            return

        self.env_data = self.env_parser.parse(template_file)
        self.env_parser.interactive_edit()
        self.env_parser.set_selected_services(self.service_parser.selected_services)

    def save_all_changes(self) -> None:
        """Save all collected changes."""
        # Use current working directory for output when running from PyInstaller
        # Check if we're running from PyInstaller temp directory
        if getattr(sys, 'frozen', False):
            # Running from PyInstaller
            self.output_dir = Path.cwd().parent / 'wikiProjects' / self.project_name
        else:
            # Running from source
            self.output_dir = self.template_dir / 'output'

        self.env_parser.set_output_directory(self.output_dir)
        # Create output dir if not exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Create config dir if not exists
        config_dir = self.output_dir / 'config'
        config_dir.mkdir(parents=True, exist_ok=True)

        self.env_parser.save(self.env_data, self.output_dir / 'config/.env')

        # Process all Jinja templates
        services_dir = self.template_dir / 'base_folder'
        if services_dir.exists():
            self.template_processor.process_directory(
                services_dir,
                self.output_dir,
                self.get_flattened_env_data()
            )

        # Generate LocalSettings.d and extension configurations
        if self.extension_changes:
            self.ext_parser._generate_localsettings(config_dir)

    def run(self) -> None:
        """Run the configuration process."""
        try:
            self.ui.display_header("W4R Configuration Tool")
            self.ui.display_info("This tool will help you configure your Wikibase instance")

            self.project_name = self.ui.prompt_string(
                "Specify a Project Name (This will also be the folder your Project-Configuration is going to be saved)",
                "Wikibase4Research"
            )

            self.collect_extension_changes()
            self.collect_environment_changes()

            self.ui.display_header("\nConfiguration Summary")
            self.ui.display_info(self.generate_summary())

            if self.ui.confirm("\nWould you like to save all these changes?", default=True):
                self.save_all_changes()
                self.ui.display_success("All changes have been saved successfully!")
                self.ui.display_info(self.generate_future_steps())
            else:
                self.ui.display_info("Configuration cancelled - no changes were saved.")

        except KeyboardInterrupt:
            self.ui.display_info("\nConfiguration cancelled by user")
        except Exception as e:
            self.ui.display_error(f"An error occurred: {str(e)}")
            raise

    def get_flattened_env_data(self) -> dict:
        flattened_data = {}
        for _, values in self.env_data.items():
            if isinstance(values, dict):
                for key, data in values.items():
                    if isinstance(data, dict) and 'value' in data:
                        flattened_data[key] = data['value']

        # Now we also append the extensions, for the composer.local.json
        flattened_data['extensions'] = self.ext_parser.get_selected_extensions_with_composer()
        #flattened_data['skins'] = self.skin_changes
        return flattened_data

def main():
    template_dir = Path(__file__).parent
    config_manager = ConfigurationManager(template_dir)
    config_manager.run()

if __name__ == "__main__":
    main()
