import io
import json
import os
import tempfile
import unittest
import urllib.error
from unittest import mock

import d4xmm
from d4xmm.nexus import account, files


def _answer(body):
    return mock.MagicMock(__enter__=lambda s: io.BytesIO(json.dumps(body).encode()),
                          __exit__=lambda *a: False)


def _http_error(code):
    return urllib.error.HTTPError("u", code, "x", {}, None)


class Check(unittest.TestCase):
    def test_gives_the_account_name_and_whether_it_is_premium(self):
        body = {"name": "PetarSpassov", "is_premium": True, "is_supporter": False}
        with mock.patch("urllib.request.urlopen", return_value=_answer(body)) as opened:
            self.assertEqual(account.check("k"), {"name": "PetarSpassov", "premium": True})
        sent = opened.call_args.args[0]
        self.assertEqual(sent.get_header("Apikey"), "k")
        # urllib keeps header names capitalised this way
        named = (sent.get_header("Application-name"), sent.get_header("Application-version"))
        self.assertEqual(named, ("D4X Mod Manager", d4xmm.__version__))

    def test_each_failure_is_named(self):
        for error, raised in ((_http_error(401), account.InvalidKey),
                              (_http_error(403), account.NotPremium),
                              (_http_error(500), files.Refused),
                              (urllib.error.URLError("down"), files.Offline)):
            with mock.patch("urllib.request.urlopen", side_effect=error):
                with self.assertRaises(raised):
                    account.check("k")


class Post(unittest.TestCase):
    def test_the_keyless_api_is_told_the_app_too(self):
        with mock.patch("urllib.request.urlopen", return_value=_answer({"data": {}})) as opened:
            files.post("{ x }", {})
        self.assertEqual(opened.call_args.args[0].get_header("Application-name"), "D4X Mod Manager")


class Download(unittest.TestCase):
    def test_the_url_is_the_first_server_listed(self):
        links = [{"name": "Nexus CDN", "URI": "https://cdn/a.zip"}, {"URI": "https://b"}]
        with mock.patch("urllib.request.urlopen", return_value=_answer(links)) as opened:
            self.assertEqual(account.download_url("k", 5, 30), "https://cdn/a.zip")
        self.assertTrue(opened.call_args.args[0].full_url.endswith(
            "/games/dunespicewars/mods/5/files/30/download_link.json"))

    def test_a_website_link_grant_goes_with_the_request(self):
        links = [{"URI": "https://cdn/a.zip"}]
        with mock.patch("urllib.request.urlopen", return_value=_answer(links)) as opened:
            account.download_url("k", 5, 30, {"key": "abc", "expires": "1700000000"})
        self.assertTrue(opened.call_args.args[0].full_url.endswith(
            "/files/30/download_link.json?key=abc&expires=1700000000"))

    def test_a_file_appears_only_once_whole(self):
        dest = os.path.join(tempfile.mkdtemp(), "a.zip")
        body = mock.MagicMock(__enter__=lambda s: io.BytesIO(b"x" * (account.CHUNK + 5)),
                              __exit__=lambda *a: False)
        with mock.patch("urllib.request.urlopen", return_value=body):
            account.fetch("https://cdn/a.zip", dest)
        self.assertEqual(os.path.getsize(dest), account.CHUNK + 5)
        self.assertFalse(os.path.exists(dest + ".part"))

    def test_spaces_in_the_address_are_escaped_and_progress_is_told(self):
        dest = os.path.join(tempfile.mkdtemp(), "a.zip")
        body = mock.MagicMock(__enter__=lambda s: io.BytesIO(b"x" * (account.CHUNK + 5)),
                              __exit__=lambda *a: False)
        seen = []
        with mock.patch("urllib.request.urlopen", return_value=body) as opened:
            account.fetch("https://cdn/7811/dsw Dyaus Anchor v1.22.zip?md5=a%2Bb&e=1", dest,
                          lambda done, total: seen.append(done))
        self.assertEqual(opened.call_args.args[0].full_url,
                         "https://cdn/7811/dsw%20Dyaus%20Anchor%20v1.22.zip?md5=a%2Bb&e=1")
        self.assertEqual(seen, [account.CHUNK, account.CHUNK + 5])

    def test_a_broken_download_leaves_nothing(self):
        dest = os.path.join(tempfile.mkdtemp(), "a.zip")
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            with self.assertRaises(files.Offline):
                account.fetch("https://cdn/a.zip", dest)
        self.assertEqual(os.listdir(os.path.dirname(dest)), [])


if __name__ == "__main__":
    unittest.main()
