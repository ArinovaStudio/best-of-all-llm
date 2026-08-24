
# pipeline.py (async, corrected)
import socket
import requests
import re
import asyncio
from playwright.async_api import async_playwright

# ---------- 1) Check connectivity ----------
def is_connected(host="8.8.8.8", port=53, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

# ---------- 2) Local IP ----------
def get_local_ip(dst_host="8.8.8.8"):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((dst_host, 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            return ip
        except Exception:
            return "unknown"

# ---------- 3) Public IP via HTTP API ----------
def get_public_ip(api="https://api.ipify.org?format=json", timeout=6):
    try:
        r = requests.get(api, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data.get("ip") or r.text.strip()
    except Exception:
        return None

# ---------- 4) Launch browser and verify browser public IP ----------
async def browser_public_ip(playwright, headless=True, proxy=None):
    browser_args = {}
    if proxy:
        browser_args["proxy"] = proxy  # {"server": "http://user:pass@host:port"}
    browser = await playwright.chromium.launch(headless=headless, **browser_args)
    page = await browser.new_page()
    try:
        await page.goto("https://api.ipify.org?format=json", timeout=15000)
        # better: get body text directly
        body_text = await page.text_content("body")
    finally:
        await browser.close()

    if not body_text:
        return None
    m = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', body_text)
    return m.group(1) if m else None

# Example browse-and-extract (keeps same pattern)
async def browse_and_extract(playwright, url, headless=True, proxy=None, wait_selector=None):
    browser_args = {}
    if proxy:
        browser_args["proxy"] = proxy
    browser = await playwright.chromium.launch(headless=headless, **browser_args)
    page = await browser.new_page()
    try:
        await page.goto(url, timeout=30000)
        if wait_selector:
            await page.wait_for_selector(wait_selector, timeout=10000)
        html = await page.content()
    finally:
        await browser.close()
    return html

# ---------- Main pipeline ----------
async def main():
    print("Checking connectivity...")
    if not is_connected():
        print("No internet connection detected. Abort.")
        return

    print("Connected to internet.")
    local_ip = get_local_ip()
    public_ip = get_public_ip() or "unknown"
    print(f"Local IP:  {local_ip}")
    print(f"Public IP: {public_ip}")

    async with async_playwright() as pw:
        print("Launching browser (headless)...")
        try:
            browser_ip = await browser_public_ip(pw, headless=True, proxy=None)
            print(f"Browser public IP (via api.ipify): {browser_ip}")
        except Exception as e:
            print(f"Error launching browser or fetching IP: {e}")

if __name__ == "__main__":
    asyncio.run(main())


