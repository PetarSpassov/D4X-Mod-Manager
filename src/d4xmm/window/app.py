"""Opening the window: python -m d4xmm.window.app"""
import json
import os

import webview
from webview.dom import DOMEventHandler

from d4xmm.window import settings
from d4xmm.window.api import Api

PAGE = os.path.join(os.path.dirname(__file__), "index.html")
HOME = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "D4XModManager")


def placement(form):
    """The window's place and un-maximised size, in the logical pixels create_window takes."""
    from System.Windows.Forms import FormWindowState  # loaded by pywebview's WinForms backend
    state = form.WindowState
    # RestoreBounds is the size un-maximising goes back to; Bounds is the screen when maximised
    bounds = form.Bounds if state == FormWindowState.Normal else form.RestoreBounds
    scale = form._scale
    return {"x": round(bounds.X / scale), "y": round(bounds.Y / scale),
            "width": round(bounds.Width / scale), "height": round(bounds.Height / scale),
            "maximized": state == FormWindowState.Maximized}


def main():
    holder = {}

    def pick_archives():
        return holder["window"].create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=True,
            file_types=("Mod archives (*.zip;*.7z;*.rar)",))

    def pick_folder(start):
        chosen = holder["window"].create_file_dialog(webview.FileDialog.FOLDER,
                                                     directory=start or "")
        return chosen[0] if chosen else None

    def on_drop(event):
        # only Python sees a dropped file's full path; the page imports through its own call()
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [f["pywebviewFullPath"] for f in files if f.get("pywebviewFullPath")]
        if paths:
            holder["window"].evaluate_js("importDropped(%s)" % json.dumps(paths))

    def bind_drop():
        holder["window"].dom.document.events.drop += DOMEventHandler(on_drop, True, True)

    def on_closing():
        # closing runs on the window's own thread, so the form can be read directly
        settings.save(HOME, window=placement(holder["window"].native))

    api = Api(HOME, pick_archives, pick_folder)
    args = settings.window_args(settings.load(HOME)["window"], webview.screens)
    holder["window"] = webview.create_window("D4X Mod Manager", PAGE, js_api=api,
                                             min_size=(560, 440), **args)
    holder["window"].events.loaded += bind_drop
    holder["window"].events.closing += on_closing
    webview.start()


if __name__ == "__main__":
    main()
