# tests/ui/test_search_flow.py
from playwright.sync_api import Page
import re

RESULT_CARD = ".results-grid .result-card"

def test_search_with_vtuber_filter(page: Page, live_server_url: str):
    # Grant clipboard perms (Chromium/WebKit)
    try:
        page.context.grant_permissions(
            ["clipboard-read", "clipboard-write"], origin=live_server_url
        )
    except Exception:
        pass  # Firefox ignores grant_permissions

    # 1. Go to index page
    page.goto(live_server_url, wait_until="domcontentloaded")

    # 2. Enter search term + tick Vtuber
    page.fill("#search_terms", "Minecraft")
    page.check('input[name="vtuber_filter"]')
    page.click('form.search-container button[type="submit"]')

    # 3. Wait for first result card and validate its title
    first_title = page.locator(f"{RESULT_CARD} h3").first.inner_text()
    assert re.search(r"Minecraft.*VTuber", first_title, re.I)

    # 4. Click Copy-Link and verify clipboard
    page.click(f"{RESULT_CARD} button.copy-button")
    clipboard_text = page.evaluate("navigator.clipboard.readText()")
    assert "https://www.youtube.com/watch?v=video123" in clipboard_text
