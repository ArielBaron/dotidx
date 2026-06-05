#!/usr/bin/env python3
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


def create_menu_display(items, selected, current, home, scroll_offset=0, search_query=""):
    console_height = console.size.height
    visible_rows = max(10, console_height - 6)

    if current < scroll_offset:
        scroll_offset = current
    elif current >= scroll_offset + visible_rows:
        scroll_offset = current - visible_rows + 1

    table = Table(
        show_header=False, show_edge=False, padding=(0, 1), expand=True, box=None
    )
    table.add_column("", width=3)
    table.add_column("", width=3)
    table.add_column("Path", style="cyan")

    for i, item in enumerate(items[scroll_offset : scroll_offset + visible_rows]):
        idx = i + scroll_offset

        marker = Text("▶", style="bold yellow") if idx == current else Text(" ")
        checkbox = (
            Text("✓", style="bold green")
            if item in selected
            else Text("○", style="dim white")
        )

        # item is already a string
        path = item.replace(home, "~") if item.startswith(home) else item

        style = "bold white on blue" if idx == current else "cyan"
        table.add_row(marker, checkbox, Text(path, style=style))

    controls = Text.assemble(
        ("↓/↑ j/k", "bold yellow"),
        " Navigate  / Exit Search   ",
        ("Space", "bold yellow"),
        " Toggle  ",
        ("a", "bold yellow"),
        " All/None  ",
        ("h", "bold yellow"),
        " Hide Selected  ",
        ("/", "bold yellow"),
        " Search  ",
        ("Enter", "bold yellow"),
        " Save  ",
        ("q", "bold yellow"),
        " Quit",
    )

    status = Text(
        f"Selected: {len(selected)}/{len(items)}",
        style="bold cyan",
    )

    footer_parts = [controls, "\n", status]
    if search_query:
        footer_parts.extend(["\n", Text(f"Search: {search_query}", style="bold magenta")])

    layout = Layout()
    layout.split_column(
        Layout(name="body"),
        Layout(name="footer", size=3 if search_query else 2),
    )

    layout["body"].update(table)
    layout["footer"].update(Text.assemble(*footer_parts))

    return layout, scroll_offset


def interactive_select(items, preselected=None, home=None):
    if preselected is None:
        preselected = set()
    if home is None:
        home = str(Path.home())

    original_items = list(items)
    items = list(items)

    selected = set(preselected)
    current = 0
    scroll_offset = 0

    all_selected = False
    hide_selected = False
    search_query = ""
    search_mode = False

    try:
        with Live(
            create_menu_display(items, selected, current, home)[0],
            console=console,
            screen=True,
            auto_refresh=False,
        ) as live:
            while True:
                display, scroll_offset = create_menu_display(
                    items, selected, current, home, scroll_offset, search_query
                )
                live.update(display)
                live.refresh()

                key = getch()

                if search_mode:
                    if  key == "\x1b[A" or key == "\x1b[B":  #  arrow keys
                        search_mode = False
                        search_query = ""
                        if hide_selected:
                            items = [i for i in original_items if i not in selected]
                        else:
                            items = list(original_items)
                        current = 0
                        scroll_offset = 0
                    elif key == "\x7f":  # Backspace
                        search_query = search_query[:-1]
                        if search_query:
                            items = [
                                i for i in original_items
                                if search_query.lower() in i.lower()
                            ]
                        else:
                            if hide_selected:
                                items = [i for i in original_items if i not in selected]
                            else:
                                items = list(original_items)
                        current = 0
                        scroll_offset = 0
                    elif key in ("\r", "\n"):
                        search_mode = False
                    elif key == " ":
                        # Space exits search mode and toggles selection
                        search_mode = False
                        search_query = ""
                        if hide_selected:
                            items = [i for i in original_items if i not in selected]
                        else:
                            items = list(original_items)
                        current = 0
                        scroll_offset = 0
                        # Now toggle the first item after exiting search
                        if items:
                            item = items[current]
                            if item in selected:
                                selected.remove(item)
                            else:
                                selected.add(item)
                    elif len(key) == 1 and key.isprintable():
                        search_query += key
                        items = [
                            i for i in original_items
                            if search_query.lower() in i.lower()
                        ]
                        current = 0
                        scroll_offset = 0
                else:
                    if key == "\x1b[A" or key == "k":
                        current = (current - 1) % len(items) if items else 0
                    elif key == "\x1b[B" or key == "j":
                        current = (current + 1) % len(items) if items else 0
                    elif key == " ":
                        if items:
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
                    elif key == "/":
                        search_mode = True
                        search_query = ""
                    elif key == "q" or key == "\x03":
                        console.print("\n[yellow]Cancelled.[/yellow]")
                        sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(0)

    return selected