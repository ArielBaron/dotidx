#!/usr/bin/env python3
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import ListView, ListItem, Label, Input, Footer
from textual.binding import Binding
from textual import on

from mime import get_installed_apps, get_current_defaults, get_browser_handlers, get_browser_defaults

MAX_RESULTS = 80


# ---------------------------------------------------------------------------
# Search screen — Input always focused, cursor tracked manually
# ---------------------------------------------------------------------------

class SearchScreen(Screen):

    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    DEFAULT_CSS = """
    SearchScreen .cursor-item Label { background: $accent; color: $text; width: 100%; }
    """

    def __init__(self, title: str, desktop_apps, terminal_apps):
        super().__init__()
        self._title = title
        self.desktop_apps = desktop_apps
        self.terminal_apps = terminal_apps
        self._cursor = 0
        self._selectable = []   # list of (value,) for each selectable row in order

    def compose(self) -> ComposeResult:
        yield Label(f" {self._title}", id="title")
        yield Input(placeholder="type to filter...", id="search")
        yield ListView(id="results")
        yield Footer()

    async def on_mount(self):
        await self._rebuild("")
        self.query_one(Input).focus()

    async def _rebuild(self, query: str):
        lv = self.query_one("#results", ListView)
        await lv.clear()
        q = query.lower()

        desktop = [(n, f) for n, f in self.desktop_apps if not q or q in n.lower()][:MAX_RESULTS]
        terminal = [n for n in self.terminal_apps if not q or q in n.lower()][:MAX_RESULTS]

        self._selectable = [f for _, f in desktop] + list(terminal)
        self._cursor = min(self._cursor, max(0, len(self._selectable) - 1))

        mount_items = []
        sel_idx = 0

        if desktop:
            hdr = ListItem(Label("-- Apps --", markup=False), disabled=True)
            hdr._sel_idx = None
            mount_items.append(hdr)
            for name, fname in desktop:
                item = ListItem(Label(name, markup=False))
                item._value = fname
                item._sel_idx = sel_idx
                if sel_idx == self._cursor:  # add class after mount — handled in _rebuild
                    item.add_class("cursor-item")
                sel_idx += 1
                mount_items.append(item)

        if terminal:
            hdr = ListItem(Label("-- Commands --", markup=False), disabled=True)
            hdr._sel_idx = None
            mount_items.append(hdr)
            for name in terminal:
                item = ListItem(Label(name, markup=False))
                item._value = name
                item._sel_idx = sel_idx
                if sel_idx == self._cursor:  # add class after mount — handled in _rebuild
                    item.add_class("cursor-item")
                sel_idx += 1
                mount_items.append(item)

        if mount_items:
            await lv.mount(*mount_items)

        self._scroll_to_cursor(lv)

    def _scroll_to_cursor(self, lv=None):
        if lv is None:
            lv = self.query_one("#results", ListView)
        for item in lv._nodes:
            if getattr(item, "_sel_idx", None) == self._cursor:
                lv.scroll_to_widget(item)
                break

    def _move_cursor(self, delta: int):
        if not self._selectable:
            return
        self._cursor = max(0, min(len(self._selectable) - 1, self._cursor + delta))
        lv = self.query_one("#results", ListView)
        for item in lv._nodes:
            idx = getattr(item, "_sel_idx", None)
            if idx is None:
                continue
            # update id for CSS highlight
            if idx == self._cursor:
                item.add_class("cursor-item")
            else:
                item.remove_class("cursor-item")
        self._scroll_to_cursor(lv)

    @on(Input.Changed)
    async def filter_changed(self, event: Input.Changed):
        self._cursor = 0
        await self._rebuild(event.value)

    def on_key(self, event) -> None:
        if event.key == "up":
            self._move_cursor(-1)
            event.stop()
        elif event.key == "down":
            self._move_cursor(1)
            event.stop()
        elif event.key == "enter":
            if self._selectable:
                self.dismiss(self._selectable[self._cursor])
            event.stop()


# ---------------------------------------------------------------------------
# Browser handlers screen
# ---------------------------------------------------------------------------

class BrowserScreen(Screen):

    BINDINGS = [
        Binding("s", "save", "Save"),
        Binding("escape,q", "cancel", "Cancel"),
    ]

    def __init__(self, handlers, desktop_apps, terminal_apps, filename_to_name):
        super().__init__()
        self.handlers = handlers
        self.desktop_apps = desktop_apps
        self.terminal_apps = terminal_apps
        self.filename_to_name = filename_to_name
        self.chosen = dict(get_browser_defaults(handlers))

    def compose(self) -> ComposeResult:
        yield ListView(id="handlers")
        yield Footer()

    async def on_mount(self):
        await self._rebuild()
        self.query_one(ListView).focus()

    async def _rebuild(self):
        lv = self.query_one("#handlers", ListView)
        await lv.clear()
        items = []
        for handler in self.handlers:
            fname = self.chosen.get(handler)
            app = self.filename_to_name.get(fname, fname) if fname else "(not set)"
            item = ListItem(Label(f"{handler:<20} {app}", markup=False))
            item._handler = handler
            items.append(item)
        if items:
            await lv.mount(*items)

    @on(ListView.Selected)
    def handler_selected(self, event: ListView.Selected):
        handler = event.item._handler
        registered = self.handlers[handler]
        registered_pairs = list(registered.items())
        extra = [(n, f) for n, f in self.desktop_apps if f not in registered.values()]

        async def on_chosen(value):
            if value is not None:
                self.chosen[handler] = value
                await self._rebuild()

        self.app.push_screen(
            SearchScreen(handler, registered_pairs + extra, self.terminal_apps),
            on_chosen,
        )

    def action_save(self):
        self.dismiss(self.chosen)

    def action_cancel(self):
        self.dismiss(None)


# ---------------------------------------------------------------------------
# Main screen
# ---------------------------------------------------------------------------

class MainScreen(Screen):

    BINDINGS = [
        Binding("s", "save", "Save"),
        Binding("q,escape", "quit_app", "Quit"),
    ]

    def __init__(self, categories, desktop_apps, terminal_apps, filename_to_name):
        super().__init__()
        self.categories = categories
        self.desktop_apps = desktop_apps
        self.terminal_apps = terminal_apps
        self.filename_to_name = filename_to_name
        self.chosen = {}
        self.browser_chosen = {}

    def compose(self) -> ComposeResult:
        yield ListView(id="cats")
        yield Footer()

    async def on_mount(self):
        self.chosen = {
            k: v
            for k, v in get_current_defaults(self.categories, self.filename_to_name).items()
            if k != "browser"
        }
        await self._rebuild()
        self.query_one(ListView).focus()

    async def _rebuild(self):
        lv = self.query_one("#cats", ListView)
        await lv.clear()
        items = []
        for cat in self.categories:
            if cat == "browser":
                text = "browser          -> configure handlers"
            else:
                fname = self.chosen.get(cat)
                app = self.filename_to_name.get(fname, fname) if fname else "(not set)"
                text = f"{cat:<14} {app}"
            item = ListItem(Label(text, markup=False))
            item._cat = cat
            items.append(item)
        if items:
            await lv.mount(*items)

    @on(ListView.Selected)
    def cat_selected(self, event: ListView.Selected):
        cat = event.item._cat

        if cat == "browser":
            handlers = get_browser_handlers()
            if not handlers:
                return

            async def on_browser_done(result):
                if result is not None:
                    self.browser_chosen.update(result)
                await self._rebuild()

            self.app.push_screen(
                BrowserScreen(handlers, self.desktop_apps, self.terminal_apps, self.filename_to_name),
                on_browser_done,
            )
        else:
            async def on_chosen(value):
                if value is not None:
                    self.chosen[cat] = value
                    await self._rebuild()

            self.app.push_screen(
                SearchScreen(cat, self.desktop_apps, self.terminal_apps),
                on_chosen,
            )

    def action_save(self):
        self.app.exit((self.chosen, self.browser_chosen))

    def action_quit_app(self):
        self.app.exit(None)


# ---------------------------------------------------------------------------
# CSS + entry points
# ---------------------------------------------------------------------------

CSS = """
Label#title {
    background: $accent;
    color: $text;
    width: 100%;
    padding: 0 1;
}
ListView {
    height: 1fr;
    border: round $primary;
}
ListItem {
    padding: 0 1;
}
ListItem.--highlight {
    background: $panel;
}
ListItem.-disabled Label {
    color: $text-muted;
    text-style: italic;
}
ListItem.cursor-item Label {
    background: $accent;
    color: $text;
    width: 100%;
}
Input {
    margin: 1 0;
}
"""


def mime_config_tui(categories):
    desktop_apps, terminal_apps, filename_to_name = get_installed_apps()

    class MimeApp(App):
        DEFAULT_CSS = CSS

        def on_mount(self):
            self.push_screen(MainScreen(
                categories, desktop_apps, terminal_apps, filename_to_name
            ))

    return MimeApp().run()


def browser_config_tui():
    desktop_apps, terminal_apps, filename_to_name = get_installed_apps()
    handlers = get_browser_handlers()
    if not handlers:
        return {}

    class BrowserApp(App):
        DEFAULT_CSS = CSS

        def on_mount(self):
            async def done(result):
                self.exit(result)
            self.push_screen(
                BrowserScreen(handlers, desktop_apps, terminal_apps, filename_to_name),
                done,
            )

    return BrowserApp().run()
