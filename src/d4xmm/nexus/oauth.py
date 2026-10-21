"""Logging in with Nexus: OAuth 2.0 with PKCE, a page the player accepts in their browser.

The tokens it gives replace the personal key: v1 and v2 both take them as a Bearer header.
"""
import base64
import hashlib
import http.server
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

from d4xmm.nexus import files

CLIENT_ID = "public_test"  # the id in Nexus's guide, until Nexus registers ours
SITE = "https://users.nexusmods.com/oauth/"
PORT = 8089
REDIRECT = "http://127.0.0.1:%d/callback" % PORT  # the callback URI registered with Nexus
WAIT = 300  # seconds the player has to accept on Nexus's page
EARLY = 60  # refresh this long before expiry, so a token can't lapse mid-download
DONE_PAGE = b"<p>Logged in. You can close this tab and go back to D4X Mod Manager.</p>"


class LoggedOut(Exception):
    """Nexus gave no tokens: the player declined, took too long, or revoked the app's access."""


def _pkce():
    """(verifier, challenge): the challenge is the verifier's SHA-256, base64url, unpadded."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    return verifier, base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def authorize_url(challenge, state):
    return SITE + "authorize?" + urllib.parse.urlencode({
        "client_id": CLIENT_ID, "response_type": "code", "scope": "", "redirect_uri": REDIRECT,
        "state": state, "code_challenge_method": "S256", "code_challenge": challenge})


def _post(fields, now=time.time):
    """Nexus's token answer, with expires_at added. Raises LoggedOut, Offline or Refused."""
    body = urllib.parse.urlencode(dict(fields, client_id=CLIENT_ID)).encode()
    headers = dict(files.HEADERS, **{"Content-Type": "application/x-www-form-urlencoded"})
    req = urllib.request.Request(SITE + "token", body, headers)
    try:
        with urllib.request.urlopen(req, timeout=files.TIMEOUT) as r:
            tokens = json.load(r)
    except urllib.error.HTTPError as e:  # an HTTPError is a URLError, so it is caught first
        if 400 <= e.code < 500:
            raise LoggedOut(str(e)) from e
        raise files.Refused(str(e)) from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise files.Offline(str(e)) from e
    return dict(tokens, expires_at=now() + tokens["expires_in"])


class _Callback(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 -- http.server's name
        url = urllib.parse.urlsplit(self.path)
        if url.path == "/callback":
            self.server.answer = dict(urllib.parse.parse_qsl(url.query))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(DONE_PAGE)

    def log_message(self, *args):
        """Nothing: the app has no console to log to."""


def _wait_for_code(server, state, wait):
    deadline = time.monotonic() + wait
    server.timeout, server.answer = 1, None
    while server.answer is None and time.monotonic() < deadline:
        server.handle_request()
    answer = server.answer or {}
    if answer.get("state") != state or "code" not in answer:
        raise LoggedOut(answer.get("error") or "no answer from Nexus's page")
    return answer["code"]


def login(open_page=webbrowser.open, wait=WAIT):
    """The player's tokens, once they accept on Nexus's page. Raises LoggedOut, OSError when
    the callback port is taken, files.Offline or files.Refused."""
    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(16)
    with http.server.HTTPServer(("127.0.0.1", PORT), _Callback) as server:
        open_page(authorize_url(challenge, state))
        code = _wait_for_code(server, state, wait)
    return _post({"grant_type": "authorization_code", "redirect_uri": REDIRECT, "scope": "",
                  "code": code, "code_verifier": verifier})


def fresh(tokens, now=time.time):
    """tokens as they are while valid, else new ones from the refresh token."""
    if now() < tokens["expires_at"] - EARLY:
        return tokens
    return _post({"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}, now)


def auth(tokens):
    """The header that authenticates a request to either API."""
    return {"Authorization": "Bearer " + tokens["access_token"]}


def account(tokens):
    """{name, premium} from the access token's claims. Not verified against Nexus's public key:
    the token came straight from Nexus over HTTPS, and Nexus checks it on every request."""
    payload = tokens["access_token"].split(".")[1]
    user = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))["user"]
    roles = user.get("membership_roles") or []
    return {"name": user.get("username"), "premium": "premium" in roles}
