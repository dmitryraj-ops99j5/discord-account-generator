import json
import random
import string
import time
import urllib.request
import urllib.error
import base64
import os

class RegistrationError(Exception):
    pass

class DiscordClient:
    REGISTER_URL = "https://discord.com/api/v9/auth/register"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, proxy=None, timeout=30):
        self.proxy = proxy
        self.timeout = timeout
        self._fingerprint = self._make_fingerprint()
        self._super_props = self._build_super_props()
        self._debug = os.environ.get("DEBUG")

    def _make_fingerprint(self):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=32))

    def _build_super_props(self):
        props = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": self.USER_AGENT,
            "browser_version": "120.0.0.0",
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 232133,
            "client_event_source": None,
        }
        return base64.b64encode(json.dumps(props).encode()).decode()

    def _build_payload(self, email, username, password, dob):
        return {
            "email": email,
            "username": username,
            "password": password,
            "date_of_birth": dob,
            "gift_code_sku_id": None,
            "captcha_key": None,
            "invite": None,
            "consent": True,
            "fingerprint": self._fingerprint,
        }

    def register(self, email, username, password, dob="1995-06-15", retries=3):
        payload = self._build_payload(email, username, password, dob)
        body = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.USER_AGENT,
            "X-Fingerprint": self._fingerprint,
            "X-Super-Properties": self._super_props,
            "X-Tracker": "0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0",
        }

        req = urllib.request.Request(self.REGISTER_URL, data=body, headers=headers, method="POST")

        proxy_handler = None
        if self.proxy:
            proxy_handler = urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy})

        for attempt in range(retries):
            try:
                if proxy_handler:
                    opener = urllib.request.build_opener(proxy_handler)
                else:
                    opener = urllib.request.build_opener()
                with opener.open(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    # print(json.dumps(data, indent=2))  # debug
                    token = data.get("token")
                    if not token:
                        raise RegistrationError(f"no token in response: {data}")
                    return token
            except urllib.error.HTTPError as e:
                body_bytes = e.read()
                body = body_bytes.decode("utf-8", errors="replace")
                if e.code == 429:
                    retry_after = int(e.headers.get("Retry-After", 5))
                    time.sleep(retry_after)
                    continue
                if e.code == 400:
                    try:
                        parsed = json.loads(body)
                        if parsed.get("captcha_key"):
                            raise RegistrationError("captcha required")
                        if parsed.get("email") and "already registered" in str(parsed.get("email")).lower():
                            raise RegistrationError("email already registered")
                    except json.JSONDecodeError:
                        pass
                raise RegistrationError(f"HTTP {e.code}: {body}")
            except urllib.error.URLError as e:
                if attempt < retries - 1:
                    time.sleep(1 + attempt)
                    continue
                raise RegistrationError(f"URL error: {e.reason}")

        raise RegistrationError("exhausted retries")
