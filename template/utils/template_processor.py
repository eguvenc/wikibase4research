from pathlib import Path
from typing import Dict, Any
from jinja2 import Template, Environment, FileSystemLoader
import shutil

class TemplateProcessor:
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            keep_trailing_newline=True
        )

    def process_template(self, template_path: Path, output_path: Path, env_data: Dict[str, Any]) -> None:
        """Process a Jinja2 template file and write the result

        Args:
            template_path: Path to the template file
            output_path: Path where to save the processed file
            env_data: Dictionary containing template variables
        """
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get the template name (relative to template_dir)
        template_name = template_path.relative_to(self.template_dir)

        # Get and render the template using the environment
        template = self.env.get_template(str(template_name))
        rendered = template.render(**env_data)

        # Write the result
        with open(output_path, 'w') as f:
            f.write(rendered)

    def copy_file(self, source_path: Path, output_path: Path) -> None:
        """Copy a non-template file to the output directory

        Args:
            source_path: Path to the source file
            output_path: Path where to save the copied file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)

    def process_directory(self, source_dir: Path, output_dir: Path, env_data: Dict[str, Any]) -> None:
        """Process all files in a directory recursively.
        For .j2 files, process them as templates.
        For other files, copy them to the output directory.

        Args:
            source_dir: Directory containing templates and other files
            output_dir: Directory where to save processed files
            env_data: Dictionary containing template variables
        """
        for source_path in source_dir.rglob('*'):
            # Skip directories, only process files
            if source_path.is_dir():
                continue

            # Calculate relative path to maintain directory structure
            relative_path = source_path.relative_to(source_dir)

            # If output_dir is not there, we create it first

            if source_path.suffix == '.j2':
                # For .j2 files, process as template and remove .j2 extension
                output_path = output_dir / relative_path.parent / relative_path.stem
                self.process_template(source_path, output_path, env_data)
            else:
                # For non-template files, just copy them
                output_path = output_dir / relative_path
                self.copy_file(source_path, output_path)
