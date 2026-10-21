import base64
import hashlib
import io
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

from d4xmm.nexus import files, oauth


def token(roles, name="Ann"):
    """An access token shaped as Nexus's: header.payload.signature, base64url."""
    claims = {"user": {"username": name, "membership_roles": roles}}
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return "h." + payload + ".s"


def _browser(answer):
    """A browser that, shown the authorize page, calls the callback with answer(its query)."""
    asked = {}

    def open_page(url):
        asked.update(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        query = urllib.parse.urlencode(answer(asked))
        threading.Thread(target=urllib.request.urlopen,
                         args=(oauth.REDIRECT + "?" + query,)).start()
    return open_page, asked


class Login(unittest.TestCase):
    def test_the_code_from_the_callback_is_exchanged_with_its_verifier(self):
        open_page, asked = _browser(lambda q: {"code": "c1", "state": q["state"]})
        with mock.patch.object(oauth, "_post", return_value={"access_token": "t"}) as post:
            self.assertEqual(oauth.login(open_page, wait=10), {"access_token": "t"})
        sent = post.call_args.args[0]
        self.assertEqual((sent["grant_type"], sent["code"]), ("authorization_code", "c1"))
        digest = hashlib.sha256(sent["code_verifier"].encode()).digest()
        self.assertEqual(asked["code_challenge"],
                         base64.urlsafe_b64encode(digest).rstrip(b"=").decode())
        self.assertEqual((asked["code_challenge_method"], asked["redirect_uri"]),
                         ("S256", oauth.REDIRECT))

    def test_an_answer_for_another_login_or_a_refusal_gives_no_tokens(self):
        for answer in (lambda q: {"code": "c1", "state": "other"},
                       lambda q: {"error": "access_denied", "state": q["state"]}):
            open_page, _ = _browser(answer)
            with mock.patch.object(oauth, "_post") as post:
                with self.assertRaises(oauth.LoggedOut):
                    oauth.login(open_page, wait=10)
            post.assert_not_called()


class Fresh(unittest.TestCase):
    TOKENS = {"access_token": "a", "refresh_token": "r", "expires_at": 1000}

    def test_a_valid_token_is_kept_and_a_due_one_refreshed(self):
        self.assertIs(oauth.fresh(self.TOKENS, now=lambda: 100), self.TOKENS)
        answer = io.BytesIO(json.dumps({"access_token": "b", "expires_in": 21600}).encode())
        with mock.patch("urllib.request.urlopen", return_value=answer) as opened:
            renewed = oauth.fresh(self.TOKENS, now=lambda: 990)
        self.assertEqual((renewed["access_token"], renewed["expires_at"]), ("b", 990 + 21600))
        sent = dict(urllib.parse.parse_qsl(opened.call_args.args[0].data.decode()))
        self.assertEqual(sent, {"grant_type": "refresh_token", "refresh_token": "r",
                                "client_id": oauth.CLIENT_ID})

    def test_a_revoked_login_is_logged_out_and_a_server_error_is_not(self):
        for code, raised in ((400, oauth.LoggedOut), (500, files.Refused)):
            error = urllib.error.HTTPError("u", code, "x", {}, None)
            with mock.patch("urllib.request.urlopen", side_effect=error):
                with self.assertRaises(raised):
                    oauth.fresh(self.TOKENS, now=lambda: 2000)


class Account(unittest.TestCase):
    def test_name_and_premium_come_from_the_token(self):
        self.assertEqual(oauth.account({"access_token": token(["member", "premium"])}),
                         {"name": "Ann", "premium": True})
        self.assertFalse(oauth.account({"access_token": token(["member"])})["premium"])
        self.assertEqual(oauth.auth({"access_token": "t"}), {"Authorization": "Bearer t"})


if __name__ == "__main__":
    unittest.main()
