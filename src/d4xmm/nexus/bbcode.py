"""A Nexus description (BBCode, with HTML line breaks and entities) as safe HTML for the window.

All text is escaped first, then only checked tags become markup: no author's text runs.
"""
import html
import re

TOKEN = re.compile(r"\[(/?)([a-z*]+)(?:=([^\]\n]*))?\]", re.I)
IMAGE = re.compile(r"\[img\]\s*(https://[^\s\"'<>\[]+)\s*\[/img\]", re.I)
BARE_LINK = re.compile(r"\[url\]\s*(https?://[^\s\"'<>\[]+)\s*\[/url\]", re.I)
LINK = re.compile(r"https?://[^\s\"'<>]+$", re.I)
COLOUR = re.compile(r"#?[0-9a-z]+$", re.I)
# tags with no value: what they open and close
PLAIN = {"b": ("<b>", "</b>"), "i": ("<i>", "</i>"), "u": ("<u>", "</u>"),
         "s": ("<s>", "</s>"), "code": ("<code>", "</code>"), "heading": ("<h4>", "</h4>"),
         "quote": ("<blockquote>", "</blockquote>"), "center": ('<div class="center">', "</div>"),
         "spoiler": ("<details><summary>Spoiler</summary>", "</details>"),
         "*": ("<li>", "</li>"), "line": ("<hr>", "")}
# a line break beside a block is the block's own, and Nexus's page shows none there
BLOCK = r"</?(?:ul|ol|li|h4|hr|details|summary|blockquote|div)\b[^>]*>"
BREAKS_BEFORE = re.compile(r"(?:<br>\s*)+(?=%s)" % BLOCK)
BREAK_AFTER = re.compile(r"(%s)\s*<br>" % BLOCK)


def _opening(name, value):
    """The opening markup for a tag that takes a value, or None to leave the tag as text."""
    value = value or ""
    if name == "size" and value[:1] in tuple("1234567"):
        return '<span class="size-%s">' % value[0]
    if name == "color" and COLOUR.match(value):
        return '<span style="color:%s">' % value
    if name == "font":
        return '<span class="mono">' if re.search("courier|mono", value, re.I) else "<span>"
    if name == "url":
        return '<a href="%s">' % value if LINK.match(value) else "<a>"
    return None


def _list(closing, value, lists):
    """[list], [list=1] or [/list]; lists is the stack of open kinds, so each closes its own."""
    if closing:
        return "</%s>" % lists.pop() if lists else ""
    lists.append("ol" if value else "ul")
    return "<%s>" % lists[-1]


def _tag(match, lists):
    """One [tag] as markup, or as written when it isn't one of ours."""
    closing, name, value = match.group(1), match.group(2).lower(), match.group(3)
    if name == "list":
        return _list(closing, value, lists)
    if name in PLAIN and value is None:
        return PLAIN[name][1 if closing else 0]
    if closing and name in ("size", "color", "font", "url"):
        return "</a>" if name == "url" else "</span>"
    found = None if closing else _opening(name, value)
    return match.group(0) if found is None else found


def to_html(bbcode):
    """The description as HTML: b, i, u, s, size, color, font, url, img, list, code, heading,
    quote, center, spoiler and line; any other [tag] stays as written, as on Nexus."""
    # each <br /> follows the line's own "\n", which is the break that's kept
    text = html.unescape(re.sub(r"<br\s*/?>", "", bbcode or "")).replace("�", "")
    text = html.escape(text.strip())
    text = IMAGE.sub(r'<img src="\1" alt="">', text)
    text = BARE_LINK.sub(r'<a href="\1">\1</a>', text)
    lists = []
    text = TOKEN.sub(lambda m: _tag(m, lists), text).replace("\n", "<br>")
    text = BREAK_AFTER.sub(r"\1", BREAKS_BEFORE.sub("", text))
    return text + "".join("</%s>" % kind for kind in reversed(lists))
