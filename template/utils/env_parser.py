from pathlib import Path
from typing import Dict, Any, Optional
import re
import socket
from .ui import UI
from .config_handler import ConfigHandler

class EnvParser(ConfigHandler):
    """Parser for environment configuration files with section support"""

    def __init__(self, template_dir: Path):
        super().__init__(template_dir)
        self.ui = UI()
        self.env_data: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.local_deployment = False

    def parse(self, env_file: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Parse the environment file and return structured data

        Args:
            env_file: Path to the environment file

        Returns:
            Dictionary containing parsed environment data organized by sections
        """
        self.env_data = {}
        current_comment = {"type": "none"}

        with open(env_file, 'r') as f:
            section_name = None
            is_section_header = False

            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('#'):
                    # Handle section headers
                    if '####' in line:
                        is_section_header = not is_section_header
                        continue
                    elif is_section_header:
                        section_match = re.match(r'#\s*(.*?)\s*#', line)
                        if section_match:
                            section_name = section_match.group(1)
                            self.env_data[section_name] = {}
                            continue

                    # Handle type comments
                    if line.startswith('##'):
                        current_comment = self._parse_type_comment(line)

                # Handle variable assignments
                if '=' in line and section_name:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    self.env_data[section_name][key] = {
                        'value': value,
                        'comment': current_comment
                    }
                    current_comment = {"type": "none"}

        return self.env_data

    def _parse_type_comment(self, line: str) -> Dict[str, Any]:
        """Parse type information from comment lines"""
        type_match = re.match(r'##\s*(.*?):', line)
        if not type_match:
            return {"type": "none"}

        type_name = type_match.group(1)
        message = re.search(r':\s*(.*)', line)
        message_text = message.group(1) if message else ""

        if type_name.startswith("list"):
            elements = re.findall(r'\[(.*?)\]', line)
            #message is everything behind the :

            return {
                "type": "list",
                "list_elements": elements[0].split(',') if elements else [],
                "message": message_text
            }
        elif type_name in ["string", "port"]:
            return {"type": type_name,
                    "message": message_text}

        return {"type": "none"}

    def save(self, env_data: Dict[str, Dict[str, Dict[str, Any]]], output_path: Path) -> None:
        """
        Save environment data to file while preserving formatting

        Args:
            env_data: Dictionary containing environment variables by section
            output_path: Path where to save the environment file
        """
        with open(output_path, 'w') as f:
            for section_name, section_vars in env_data.items():
                # Write section header
                f.write(self._format_section_header(section_name))
                f.write('\n')

                # Write section variables
                for var_name, var_info in section_vars.items():
                    f.write(self._format_variable(var_name, var_info))
                    f.write('\n')

                # Add separator between sections
                f.write('\n')

    def _format_section_header(self, section_name: str) -> str:
        """Format section header with proper padding"""
        header = []
        header.append("# " + "#" * 39 + " #")
        header.append(f"# {section_name:<38} #")
        header.append("# " + "#" * 38 + "  #")
        return '\n'.join(header)

    def _format_variable(self, name: str, info: Dict[str, Any]) -> str:
        """Format a variable with its type comment and value"""
        lines = []

        # Add type comment if exists
        if info['comment']['type'] != 'none':
            if info['comment']['type'] == 'list':
                elements = ','.join(info['comment']['list_elements'])
                lines.append(f"## list[{elements}]:")
            else:
                lines.append(f"## {info['comment']['type']}:")

        # Format value
        value = info['value']
        if self._needs_quotes(value):
            value = f'"{value}"'

        lines.append(f"{name}={value}")
        return '\n'.join(lines)

    def _needs_quotes(self, value: str) -> bool:
        """Check if a value needs to be quoted"""
        return any(char in value for char in ' =#$')

    def _check_hosts_entry(self, domain: str) -> bool:
        """Check if domain exists in /etc/hosts file."""
        self.ui.clear_screen()
        self.ui.display_header("Local Development Setup")
        self.ui.display_info("\nChecking local domain configuration...")

        result = False
        with self.ui.with_loading_animation(f"Resolving {domain} in hosts file"):
            try:
                result = socket.gethostbyname(domain) == "127.0.0.1"
            except socket.gaierror:
                result = False

        if not result:
            self.ui.display_warning(f"Domain {domain} is not configured in your hosts file")
            self.ui.display_info("\nTo run Wikibase locally, you need to map this domain to localhost.")
            choice = self.ui.prompt_radio(
                ["Skip for now - I'll set it up later",
                 "Show me the command to add it manually",
                 "Add it automatically (requires sudo)"],
                "How would you like to configure the hosts file?"
            )

            if choice == "Show me the command to add it manually":
                command = f"sudo sh -c 'echo \"127.0.0.1 {domain}\" >> /etc/hosts'"
                self.ui.display_header("Manual Configuration")
                self.ui.display_info("\nRun this command in your terminal to add the hosts entry:")
                self.ui.display_dict({"Command": command})
                self.ui.display_info("\nAfter running the command, the domain will resolve to your local machine.")
                self.ui.continue_on_input()
            elif choice == "Add it automatically (requires sudo)":
                import subprocess
                try:
                    cmd = f'echo "127.0.0.1 {domain}" | sudo tee -a /etc/hosts'
                    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                    if result.returncode == 0:
                        self.ui.display_success(f"Successfully configured {domain} for local development")
                        self.ui.display_info("Your domain is now properly mapped to localhost (127.0.0.1)")
                        return True
                    else:
                        self.ui.display_error("Failed to modify hosts file")
                        self.ui.display_dict({"Error": result.stderr})
                except Exception as e:
                    self.ui.display_error("Failed to configure local domain")
                    self.ui.display_dict({"Error": str(e)})

        return result

    def interactive_edit(self) -> None:
        """Interactive environment variable editing"""
        # Ask about local deployment first
        self.ui.display_header("Environment Configuration")
        self.local_deployment = self.ui.confirm("Do you want to deploy locally?", default=False)

        for section_name, section_vars in self.env_data.items():
            for var_name, var_info in section_vars.items():
                var_type = var_info['comment']['type']
                new_value = var_info['value']
                # Get message from comment if available, otherwise use var_name
                comment_msg = var_info['comment'].get('message', '')
                prompt_msg = f"{comment_msg}({var_name})" if comment_msg else var_name

                # Clear screen and show header for each variable
                self.ui.display_header(f"Configure: {var_name}")

                if var_type == 'string':
                    new_value = self.ui.prompt_string(prompt_msg, var_info['value'])
                    # Check hosts entry for server name if deploying locally
                    if self.local_deployment and var_name == 'W4R_SERVER_NAME':
                        self._check_hosts_entry(new_value)

                elif var_type.startswith('list'):
                    new_value = self.ui.prompt_choice(
                        prompt_msg,
                        var_info['comment']['list_elements'],
                        var_info['value']
                    )
                elif var_type == 'port':
                    new_value = self.ui.prompt_port(prompt_msg, var_info['value'])

                if new_value != var_info['value']:
                    var_info['value'] = new_value
                    self.ui.display_success(f"Updated {var_name}")

    def set_selected_services(self, services: set[str]):
        #split services into comma separated list w/o whitespace
        selected_services = [service.strip() for service in services]
        self.env_data['INSTANCE Settings']['W4R_COMPOSER_SERVICE_INCLUDE']['value']=','.join(selected_services)

    def set_output_directory(self, directory: Path):
        try:
            # Try to get relative path from current working directory
            relative_path = directory.relative_to(Path.cwd())
            self.env_data['INSTANCE Settings']['W4R_INIT_FOLDER']['value'] = str(relative_path)
        except ValueError:
            # If relative path fails, use absolute path
            self.env_data['INSTANCE Settings']['W4R_INIT_FOLDER']['value'] = str(directory.resolve())

def main():
    parser = EnvParser(Path(__file__).parent.parent)
    env_file = parser.template_dir / '.env'

    if not env_file.exists():
        parser.ui.display_error(f"Environment file not found: {env_file}")
        return

    parser.parse(env_file)
    parser.interactive_edit()
    parser.save(parser.env_data, env_file)
    parser.ui.display_success("Environment configuration saved successfully")

if __name__ == "__main__":
    main()
