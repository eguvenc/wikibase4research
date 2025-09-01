from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.style import Style
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from beaupy import select, select_multiple
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from typing import Optional, List, Dict, Any
import threading
import time

class UI:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        self.styles = {
            'header': Style(color="yellow", bold=True),
            'info': Style(color="cyan"),
            'success': Style(color="green", bold=True),
            'error': Style(color="red", bold=True),
            'warning': Style(color="yellow"),
            'highlight': Style(color="magenta", bold=True),
            'dim': Style(color="grey70"),
        }

    def clear_screen(self) -> None:
        """Clear the terminal screen"""
        self.console.clear()

    def display_header(self, text: str, cls: bool=True) -> None:
        """Display a header section"""
        if cls: self.console.clear()
        self.console.print(Text(text, style=self.styles['header']))

    def continue_on_input(self):
        """Wait for user input before continuing"""
        self.console.print(Text("Press Enter to continue...", style=self.styles['info']))
        self.console.input()

    def display_info(self, text: str) -> None:
        """Display information text"""
        self.console.print(Text(text, style=self.styles['info']))

    def display_success(self, text: str) -> None:
        """Display success message"""
        self.console.print(Panel(
            Text(f"✓ {text}", style=self.styles['success']),
            border_style="green",
            expand=False
        ))

    def display_error(self, text: str) -> None:
        """Display error message"""
        self.console.print(Panel(
            Text(f"✗ {text}", style=self.styles['error']),
            border_style="red",
            expand=False
        ))

    def display_list(self, items: List[str], title: str = "") -> None:
        """Display a list of items with optional title"""
        if title:
            self.display_header(title)

        table = Table(show_header=False, show_edge=False, box=None)
        table.add_column("", style=self.styles['info'])

        for item in items:
            table.add_row(f"• {item}")

        self.console.print(table)

    def display_dict(self, data: Dict[str, Any], title: str = "") -> None:
        """Display a dictionary as a table"""
        table = Table(
            title=title if title else None,
            title_style=self.styles['header'],
            show_header=True,
            header_style=self.styles['highlight'],
            border_style=self.styles['dim']
        )

        for key, value in data.items():
            table.add_row(str(key), str(value))

        self.console.print(table)

    def prompt_choice(self,
                     message: str,
                     choices: List[str],
                     default: str = None) -> str:
        """Prompt user for a choice with autocompletion"""

        return self.prompt_radio(choices, message)

    def prompt_string(self,
                     message: str,
                     default: str = None,
                     show_default: bool = True) -> str:
        """Prompt for string input"""
        return Prompt.ask(
            message + "\n",
            default=default,
            show_default=show_default
        )

    def prompt_port(self, message: str, default: str = None) -> str:
        """Prompt for port number with validation"""
        while True:
            value = self.prompt_string(message, default)

            if not value.isdigit():
                self.display_error("Please enter a valid port number (80, 443, or above 1024)")
                continue

            port = int(value)
            if port == 80 or port == 443 or port > 1024:
                return value
            self.display_error("Invalid port. Must be 80, 443, or above 1024.")

    def prompt_list(self,
                   message: str,
                   options: List[str],
                   current_value: str = "",
                   allow_multiple: bool = True) -> str:
        """Prompt for list selection"""
        completer = WordCompleter(options)

        self.display_info(f"Current value: {current_value}")
        self.display_info("Available options: " + ", ".join(options))

        prompt_text = (f"{message}\n"
                      f"{'(comma-separated for multiple) ' if allow_multiple else ''}"
                      "or press Enter to keep current: ")

        new_value = prompt(prompt_text, completer=completer).strip()
        return new_value if new_value else current_value

    def confirm(self, message: str, default: bool = True) -> bool:
        """Prompt for confirmation"""
        return Prompt.ask(
            message,
            choices=["y", "n"],
            default="y" if default else "n"
        ).lower() == "y"

    def prompt_checkbox(self,
                           options: List[str],
                           message: str = "Select options:",
                           default_selected: List[int] = None) -> List[str]:
            """
            Display a checkbox-style multiple selection prompt

            Args:
                options: List of options to choose from
                message: Prompt message to display
                default_selected: List of indices that should be selected by default

            Returns:
                List of selected options
            """
            self.display_header(message)
            selected = select_multiple(
                options,
                tick_character='✓',
                ticked_indices=default_selected or [],
                cursor_style="cyan"
            )
            return selected

    def prompt_radio(self,
                    options: List[str],
                    message: str = "Select an option:",
                    default_index: int = 0) -> str:
        """
        Display a radio-style single selection prompt

        Args:
            options: List of options to choose from
            message: Prompt message to display
            default_index: Index of the default selected option

        Returns:
            Selected option
        """
        self.display_header(message, False)
        selected = select(
            options,
            cursor="●",
            cursor_style="cyan",
            cursor_index=default_index
        )
        return selected

    def display_warning(self, text: str) -> None:
        """Display warning message

        Args:
            text: The warning message to display
        """
        self.console.print(Panel(
            Text(f"⚠ {text}", style=self.styles['warning']),
            border_style="yellow",
            expand=False
        ))

    def with_loading_animation(self, message: str = "Loading..."):
        """Context manager for loading animation

        Args:
            message: Message to display while loading

        Usage:
            with ui.with_loading_animation("Processing..."):
                # do some work
        """
        class LoadingContext:
            def __init__(self, console, message):
                self.console = console
                self.message = message
                self.live = None

            def __enter__(self):
                spinner = Spinner("dots", text=self.message, style="cyan")
                self.live = Live(
                    spinner,
                    console=self.console,
                    refresh_per_second=10,
                    transient=True
                )
                self.live.__enter__()
                return self.live

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.live:
                    self.live.__exit__(exc_type, exc_val, exc_tb)

        return LoadingContext(self.console, message)
