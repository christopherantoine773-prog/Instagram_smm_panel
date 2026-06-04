import time
import requests
import random
import string
import re

class EmailVerifier:
    def __init__(self, logger=None):
        self.logger = logger or print
        self.domain = "1secmail.com"
        self.login = self._generate_login()
        self.email = f"{self.login}@{self.domain}"
        self.logger(f"[EMAIL] Generated temporary email: {self.email}")

    def _generate_login(self, length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_email(self):
        return self.email

    def get_verification_link(self, timeout=120):
        self.logger(f"[EMAIL] Polling inbox for verification email on {self.email}...")
        elapsed = 0
        poll_interval = 5

        while elapsed < timeout:
            try:
                resp = requests.get(
                    "https://www.1secmail.com/api/v1/",
                    params={
                        "action": "getMessages",
                        "login": self.login,
                        "domain": self.domain
                    },
                    timeout=10
                )
                resp.raise_for_status()
                messages = resp.json()
                
                if messages:
                    msg_id = messages[0]['id']
                    self.logger(f"[EMAIL] Message detected (ID: {msg_id}). Reading content...")
                    msg_resp = requests.get(
                        "https://www.1secmail.com/api/v1/",
                        params={
                            "action": "readMessage",
                            "login": self.login,
                            "domain": self.domain,
                            "id": msg_id
                        },
                        timeout=10
                    )
                    msg_resp.raise_for_status()
                    msg_data = msg_resp.json()
                    body = msg_data.get('body', '')
                    
                    link = self._extract_link(body)
                    if link:
                        self.logger(f"[EMAIL] Verification link extracted: {link}")
                        return link
            except Exception as e:
                self.logger(f"[EMAIL] Error polling mail inbox: {e}")

            time.sleep(poll_interval)
            elapsed += poll_interval

        self.logger("[EMAIL] Timeout waiting for verification email.")
        raise TimeoutError("No verification email arrived within timeout period.")

    def _extract_link(self, text):
        # Match Instagram verify URL
        match = re.search(r'https://(www\.)?instagram\.com/accounts/confirm_email/[^"\s]+', text)
        if match:
            return match.group(0)
        return None
