# Wikibase4Research Configuration Tool

This is a CLI tool that helps users configure their Wikibase4Research instance through an interactive interface. The tool handles extension selection, environment configuration, and service setup.

## Development Setup

1. Install dependencies using `uv`:
   ```bash
   uv pip install -r requirements.txt
   ```

   Or install directly from pyproject.toml:
   ```bash
   uv pip install .
   ```

2. The project uses Python 3.13+ and depends on:
   - beaupy - for interactive CLI components
   - jinja2 - for template processing
   - prompt-toolkit - for enhanced CLI prompts
   - python-dotenv - for .env file handling
   - rich - for terminal formatting
   - PyInstaller - for creating standalone executables

## Project Structure

- `config.py` - Main entry point and configuration manager
- `utils/` - Core functionality modules:
  - `env_parser.py` - Handles environment variable configuration
  - `extension_parser.py` - Manages MediaWiki extension selection
  - `service_parser.py` - Handles service configuration
  - `template_processor.py` - Processes Jinja2 templates
  - `ui.py` - Unified interface components
  - `file_manager.py` - File operations handler

## Running the Tool

Development mode:
```bash
uv run config.py
```

Build executable:
```bash
uv run pyinstaller w4r-config.spec
```

The spec file ensures all necessary templates and configurations are included in the final executable.

## Working Directory

When running from source (`config.py`), the tool uses `template_dir` as its base.
When running the compiled executable, it uses the current working directory's parent folder to create a new project in `wikiProjects/<project_name>`.

## Git

Remember to keep `.venv/` and `.ropeproject/` in your `.gitignore` as they contain environment-specific files.
