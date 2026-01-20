#!/usr/bin/env python3
"""Interactive UI components for dotidx using Rich TUI."""

import sys
from pathlib import Path
import tty
import termios

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

console = Console()


def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch += sys.stdin.read(2)
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def create_menu_display(items, selected, current, home, scroll_offset=0):
    console_height = console.size.height
    visible_rows = max(10, console_height - 10)

    if current < scroll_offset:
        scroll_offset = current
    elif current >= scroll_offset + visible_rows:
        scroll_offset = current - visible_rows + 1

    table = Table(show_header=False, show_edge=False, padding=(0, 1), expand=True, box=None)
    table.add_column("", width=3)
    table.add_column("", width=3)
    table.add_column("Path", style="cyan")

    for i, item in enumerate(items[scroll_offset:scroll_offset + visible_rows]):
        idx = i + scroll_offset

        marker = Text("▶", style="bold yellow") if idx == current else Text(" ")
        checkbox = Text("✓", style="bold green") if item in selected else Text("○", style="dim white")

        try:
            path = f"~/{item.relative_to(home)}"
        except ValueError:
            path = str(item)

        style = "bold white on blue" if idx == current else "cyan"
        table.add_row(marker, checkbox, Text(path, style=style))

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(
        Panel("[bold cyan]Select Dotfiles to Track[/bold cyan]", style="bold white on blue")
    )

    controls = Text.assemble(
        ("↑/↓", "bold yellow"), " Navigate  ",
        ("Space", "bold yellow"), " Toggle  ",
        ("a", "bold yellow"), " All/None  ",
        ("h", "bold yellow"), " Hide Selected  ",
        ("Enter", "bold yellow"), " Save  ",
        ("q", "bold yellow"), " Quit",
    )

    status = Text(
        f"Selected: {len(selected)}/{len(items)}",
        style="bold cyan",
    )

    layout["body"].update(Panel(table, padding=(1, 2)))
    layout["footer"].update(Panel(Text.assemble(controls, "\n", status)))

    return layout, scroll_offset


def interactive_select(items, preselected=None, home=None):
    if preselected is None:
        preselected = set()
    if home is None:
        home = Path.home()

    original_items = list(items)
    items = list(items)

    selected = set(preselected)
    current = 0
    scroll_offset = 0

    all_selected = False
    hide_selected = False

    try:
        with Live(
            create_menu_display(items, selected, current, home)[0],
            console=console,
            screen=True,
            auto_refresh=False,
        ) as live:
            while True:
                display, scroll_offset = create_menu_display(
                    items, selected, current, home, scroll_offset
                )
                live.update(display)
                live.refresh()

                key = getch()

                if key == "\x1b[A":
                    current = (current - 1) % len(items)
                elif key == "\x1b[B":
                    current = (current + 1) % len(items)

                elif key == " ":
                    item = items[current]
                    if item in selected:
                        selected.remove(item)
                    else:
                        selected.add(item)

                elif key in ("\r", "\n"):
                    break

                elif key == "a":
                    if all_selected:
                        selected.clear()
                        all_selected = False
                    else:
                        selected = set(items)
                        all_selected = True

                elif key == "h":
                    hide_selected = not hide_selected
                    if hide_selected:
                        items = [i for i in original_items if i not in selected]
                    else:
                        items = list(original_items)
                    current = 0
                    scroll_offset = 0

                elif key == "q" or key == "\x03":
                    console.print("\n[yellow]Cancelled.[/yellow]")
                    sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(0)

    return selected


def show_success(msg):
    console.print(f"[bold green]✓[/bold green] {msg}")


def show_error(msg):
    console.print(f"[bold red]✗[/bold red] {msg}")


def show_info(msg):
    console.print(f"[bold cyan]ℹ[/bold cyan] {msg}")


def show_warning(msg):
    console.print(f"[bold yellow]⚠[/bold yellow] {msg}")