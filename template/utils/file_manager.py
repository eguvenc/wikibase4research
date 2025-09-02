from pathlib import Path
from typing import Dict, Any, Union, List
import shutil
from jinja2 import Environment, FileSystemLoader

class FileManager:
    """Centralized file manager for all file operations in the application."""
    
    def __init__(self, project_root: Path):
        """Initialize the file manager with project root directory.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.output_root = project_root / 'output'
        
        # Initialize Jinja environment for template processing
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(project_root)),
            keep_trailing_newline=True
        )
        
        # Ensure output directory exists
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Standard output directories
        self._output_dirs = {
            'env': self.output_root / 'env',            # Environment files
            'extensions': self.output_root / 'extensions', # Extension configs
            'services': self.output_root / 'services',   # Service configs
            'templates': self.output_root / 'templates', # Processed templates
            'scripts': self.output_root / 'scripts'      # Script files
        }
        
        # Create standard directories
        for directory in self._output_dirs.values():
            directory.mkdir(parents=True, exist_ok=True)

    def get_output_path(self, category: str) -> Path:
        """Get the path to a specific output category directory.
        
        Args:
            category: Category of output ('env', 'extensions', 'services', 'templates', 'scripts')
            
        Returns:
            Path to the requested output directory
        """
        if category not in self._output_dirs:
            raise ValueError(f"Unknown output category: {category}")
        return self._output_dirs[category]

    def write_file(self, path: Union[str, Path], content: str) -> None:
        """Write content to a file, creating parent directories if needed.
        
        Args:
            path: Path where to write the file
            content: Content to write
        """
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)

    def read_file(self, path: Union[str, Path]) -> str:
        """Read content from a file.
        
        Args:
            path: Path to the file to read
            
        Returns:
            Content of the file
        """
        with open(path, 'r') as f:
            return f.read()

    def copy_file(self, source: Union[str, Path], dest: Union[str, Path]) -> None:
        """Copy a file from source to destination, creating parent directories if needed.
        
        Args:
            source: Source file path
            dest: Destination file path
        """
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

    def process_template(self, template_path: Union[str, Path], output_path: Union[str, Path], 
                        context: Dict[str, Any]) -> None:
        """Process a Jinja template and write the result.
        
        Args:
            template_path: Path to the template file
            output_path: Path where to save the processed file
            context: Dictionary containing template variables
        """
        template_path = Path(template_path)
        output_path = Path(output_path)
        
        # Get template name relative to project root
        template_name = template_path.relative_to(self.project_root)
        
        # Process template
        template = self.jinja_env.get_template(str(template_name))
        rendered = template.render(**context)
        
        # Write output
        self.write_file(output_path, rendered)

    def process_directory(self, source_dir: Union[str, Path], output_dir: Union[str, Path], 
                         context: Dict[str, Any]) -> None:
        """Process all files in a directory recursively.
        
        Args:
            source_dir: Directory containing files to process
            output_dir: Directory where to save processed files
            context: Dictionary containing template variables for .j2 files
        """
        source_dir = Path(source_dir)
        output_dir = Path(output_dir)
        
        for source_path in source_dir.rglob('*'):
            if source_path.is_dir():
                continue
                
            relative_path = source_path.relative_to(source_dir)
            
            if source_path.suffix == '.j2':
                # Process templates
                output_path = output_dir / relative_path.parent / relative_path.stem
                self.process_template(source_path, output_path, context)
            else:
                # Copy other files
                output_path = output_dir / relative_path
                self.copy_file(source_path, output_path)

    def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List files in a directory matching a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Glob pattern to match files against
            
        Returns:
            List of matching file paths
        """
        return list(Path(directory).glob(pattern))

    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Path to the directory
            
        Returns:
            Path to the created/existing directory
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def delete_directory(self, path: Union[str, Path], recursive: bool = True) -> None:
        """Delete a directory and optionally its contents.
        
        Args:
            path: Path to the directory to delete
            recursive: If True, delete directory contents recursively
        """
        path = Path(path)
        if recursive and path.exists():
            shutil.rmtree(path)
        elif path.exists():
            path.rmdir()

    def clear_output(self) -> None:
        """Clear all output directories."""
        self.delete_directory(self.output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Recreate standard directories
        for directory in self._output_dirs.values():
            directory.mkdir(parents=True, exist_ok=True)

    def get_project_root(self) -> Path:
        """Get the project root directory.
        
        Returns:
            Path to the project root directory
        """
        return self.project_root

    def get_output_root(self) -> Path:
        """Get the output root directory.
        
        Returns:
            Path to the output root directory
        """
        return self.output_root