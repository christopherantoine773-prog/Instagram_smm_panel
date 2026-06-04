import time
import requests
from panel.bot_logic.settings_helper import get_setting

class CaptchaSolver:
    def __init__(self, logger=None):
        self.logger = logger or print
        
    def get_api_key(self):
        return get_setting("captcha_api_key", "")

    def is_captcha_present(self, page):
        try:
            content = page.content().lower()
            return "captcha" in content or "recaptcha" in content or "iframe[src*='recaptcha']" in content
        except Exception:
            return False

    def solve(self, page):
        api_key = self.get_api_key()
        if not api_key or api_key == "YOUR_CAPMONSTER_API_KEY":
            self.logger("[CAPTCHA] API Key not configured. Skipping or failing captcha step.")
            return False

        if not self.is_captcha_present(page):
            self.logger("[CAPTCHA] No captcha detected.")
            return True

        self.logger("[CAPTCHA] Captcha detected. Initiating solve via CapMonster...")
        try:
            sitekey = self._extract_sitekey(page)
            if not sitekey:
                self.logger("[CAPTCHA] Sitekey could not be extracted.")
                return False

            task_payload = {
                "clientKey": api_key,
                "task": {
                    "type": "NoCaptchaTaskProxyless",
                    "websiteURL": page.url,
                    "websiteKey": sitekey
                }
            }

            base_url = "https://api.capmonster.cloud"
            response = requests.post(f"{base_url}/createTask", json=task_payload, timeout=15)
            response.raise_for_status()
            task_id = response.json().get("taskId")
            
            if not task_id:
                self.logger(f"[CAPTCHA] Failed to create task: {response.text}")
                return False

            # Wait for results
            elapsed = 0
            timeout = 120
            while elapsed < timeout:
                resp = requests.post(f"{base_url}/getTaskResult", json={
                    "clientKey": api_key,
                    "taskId": task_id
                }, timeout=10)
                resp.raise_for_status()
                result = resp.json()
                
                if result.get("status") == "ready":
                    token = result["solution"]["gRecaptchaResponse"]
                    self.logger("[CAPTCHA] Token received. Injecting token into page...")
                    page.evaluate(f'document.getElementById("g-recaptcha-response").innerHTML="{token}";')
                    page.evaluate('() => { document.querySelector("form").submit(); }')
                    return True
                
                time.sleep(5)
                elapsed += 5

            self.logger("[CAPTCHA] Captcha solving timed out.")
            return False

        except Exception as e:
            self.logger(f"[CAPTCHA] Error solving captcha: {e}")
            return False

    def _extract_sitekey(self, page):
        try:
            content = page.content()
            # Look for sitekey in data-sitekey attribute
            import re
            match = re.search(r'data-sitekey=["\']([A-Za-z0-9_\-]+)["\']', content)
            if match:
                sitekey = match.group(1)
                self.logger(f"[CAPTCHA] Extracted sitekey: {sitekey}")
                return sitekey
            
            # Alternative search pattern
            match = re.search(r'sitekey["\']:\s*["\']([A-Za-z0-9_\-]+)["\']', content)
            if match:
                sitekey = match.group(1)
                self.logger(f"[CAPTCHA] Extracted sitekey: {sitekey}")
                return sitekey
        except Exception as e:
            self.logger(f"[CAPTCHA] Error extracting sitekey: {e}")
        return None
