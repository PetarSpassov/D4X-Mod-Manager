"""Opening the window: python -m d4xmm.window.app"""
import os

import webview

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

    api = Api(HOME, steam.find(), pick_archives)
    holder["window"] = webview.create_window("D4X Mod Manager", PAGE, js_api=api,
                                             width=760, height=620, min_size=(520, 420))
    webview.start()


if __name__ == "__main__":
    main()
