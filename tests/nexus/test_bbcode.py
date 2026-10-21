import unittest

from d4xmm.nexus.bbcode import to_html


class ToHtml(unittest.TestCase):
    def test_text_styles_sizes_and_colours_become_markup(self):
        self.assertEqual(to_html("[size=5][b]Big[/b][/size] [i]it[/i] [u]u[/u] [s]s[/s] "
                                 "[color=#cc0000]red[/color] [font=Courier New]x[/font]"),
                         '<span class="size-5"><b>Big</b></span> <i>it</i> <u>u</u> <s>s</s> '
                         '<span style="color:#cc0000">red</span> <span class="mono">x</span>')

    def test_lines_break_but_not_beside_a_list(self):
        self.assertEqual(to_html("Intro\n<br />\n<br />[list]\n<br />[*]One\n<br />[*]Two\n"
                                 "<br />[/list]\n<br />After\n<br />[list=1][*]A[/list]"),
                         "Intro<ul><li>One<li>Two</ul>After<ol><li>A</ol>")

    def test_links_and_images_keep_only_web_addresses(self):
        self.assertEqual(to_html("[url=https://discord.gg/x]Discord[/url] "
                                 "[url=javascript:alert(1)]bad[/url] "
                                 "[url]https://a.b/c[/url] [img]https://x/1.jpg[/img]"),
                         '<a href="https://discord.gg/x">Discord</a> <a>bad</a> '
                         '<a href="https://a.b/c">https://a.b/c</a> '
                         '<img src="https://x/1.jpg" alt="">')

    def test_html_written_by_the_author_is_shown_as_text(self):
        self.assertEqual(to_html('&lt;script&gt;x&lt;/script&gt; <b onclick="y">'),
                         "&lt;script&gt;x&lt;/script&gt; &lt;b onclick=&quot;y&quot;&gt;")

    def test_a_value_cannot_break_out_of_its_attribute(self):
        self.assertEqual(to_html('[color=red" onmouseover="x]t[/color]'),
                         '[color=red&quot; onmouseover=&quot;x]t</span>')

    def test_unknown_tags_stay_as_written_and_open_lists_are_closed(self):
        self.assertEqual(to_html("[Done] X&#92;Steam [list][*]a"), "[Done] X\\Steam <ul><li>a</ul>")

    def test_spoilers_code_and_headings(self):
        self.assertEqual(to_html("[heading]H[/heading][spoiler]s[/spoiler][code]c[/code]"),
                         "<h4>H</h4><details><summary>Spoiler</summary>s</details><code>c</code>")


if __name__ == "__main__":
    unittest.main()
