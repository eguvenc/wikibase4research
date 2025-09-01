from pathlib import Path
from typing import List, Set, Optional
from .ui import UI
import glob

class ServiceParser:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.ui = UI()
        self.selected_services: Set[str] = {"wiki"}  # wiki is always selected
        self.available_services: Optional[List[str]] = None

    def get_available_services(self) -> List[str]:
        """Find all available services from compose files"""
        services = {"wiki"}  # Start with wiki service is always required
        compose_files = glob.glob(str(self.base_dir / "compose-*.yml"))

        for file in compose_files:
            # Extract service name from filename (compose-<service>.yml)
            service = Path(file).stem.replace('compose-', '')
            if service != "wiki":  # Skip wiki as it's already added
                services.add(service)

        return sorted(list(services))

    def select_services(self, required_services: Set[str] = set()) -> None:
        """Interactive service selection with required services pre-selected"""
        if self.available_services is None:
            self.available_services = self.get_available_services()

        service_descriptions = {
            "wiki": "Core Wikibase service (always enabled)",
            "wdqs": "Wikidata Query Service - Enables SPARQL querying",
            "openrefine": "OpenRefine Reconciliation Service",
            "kompakkt": "3D Object Viewer",
            "elasticsearch": "Enhanced search capabilities",
            "wbjobrunner": "Background job processing"
        }

        # First show required services if any
        if required_services:
            self.ui.display_info("\nRequired services based on selected extensions:")
            for service in sorted(required_services):
                desc = service_descriptions.get(service, "Required service")
                self.ui.display_info(f"  • {service}: {desc}")

        # Set default services (required + wiki)
        default_services = {"wiki"} | required_services
        self.selected_services = default_services.copy()

        # Ask if user wants to customize service selection
        if self.ui.confirm("\nWould you like to customize the service selection?", default=False):
            self.ui.display_info("\nAvailable services:")
            for service in self.available_services:
                desc = service_descriptions.get(service, "Additional service")
                self.ui.display_info(f"  • {service}: {desc}")

            # Prepare default selections for checkbox
            default_selected = []
            for i, service in enumerate(self.available_services):
                if service in default_services:
                    default_selected.append(i)

            # Show selection prompt
            selected = self.ui.prompt_checkbox(
                self.available_services,
                "\nSelect services to enable (wiki is mandatory):",
                default_selected=default_selected
            )

            # Update selected services ensuring required ones are included
            self.selected_services = set(selected) | default_services

        # Show final selection
        self.ui.display_success("\nSelected services:")
        for service in sorted(self.selected_services):
            desc = service_descriptions.get(service, "")
            self.ui.display_info(f"  • {service}{': ' + desc if desc else ''}")

    def get_selected_services(self) -> Set[str]:
        """Return the set of selected services"""
        return self.selected_services
