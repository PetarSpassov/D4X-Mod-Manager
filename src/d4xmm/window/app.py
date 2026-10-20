"""Opening the window: python -m d4xmm.window.app"""
import json
import os

import webview
from webview.dom import DOMEventHandler

from d4xmm.game import steam
from d4xmm.window.api import Api

PAGE = os.path.join(os.path.dirname(__file__), "index.html")
HOME = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "D4XModManager")


def main():
    holder = {}

    def pick_archives():
        return holder["window"].create_file_dialog(
            webview.FileDialog.OPEN, allow_multiple=True,
            file_types=("Mod archives (*.zip;*.7z;*.rar)",))

    def on_drop(event):
        # only Python sees a dropped file's full path; the page imports through its own call()
        files = event.get("dataTransfer", {}).get("files", [])
        paths = [f["pywebviewFullPath"] for f in files if f.get("pywebviewFullPath")]
        if paths:
            holder["window"].evaluate_js("importDropped(%s)" % json.dumps(paths))

    def bind_drop():
        holder["window"].dom.document.events.drop += DOMEventHandler(on_drop, True, True)

    api = Api(HOME, steam.find(), pick_archives)
    holder["window"] = webview.create_window("D4X Mod Manager", PAGE, js_api=api,
                                             width=860, height=640, min_size=(560, 440))
    holder["window"].events.loaded += bind_drop
    webview.start()


if __name__ == "__main__":
    main()
