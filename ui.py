#!/usr/bin/env python3
import rich
from rich.console import Console

console = Console()

def show_success(msg):
    console.print(f"[bold green]✓[/bold green] {msg}")

def show_error(msg):
    console.print(f"[bold red]✗[/bold red] {msg}")

def show_info(msg):
    console.print(f"[bold cyan]ℹ[/bold cyan] {msg}")

def show_warning(msg):
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
