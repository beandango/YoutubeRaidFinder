# tests/ui/test_smoke.py
from playwright.sync_api import Page

def test_add_and_remove_favorite(page: Page, live_server_url: str):
    page.goto(live_server_url, wait_until="domcontentloaded")

    # Wait until the search UI is ready
    page.wait_for_selector("#favorite-channel-input", state="visible")

    # Add a favorite channel
    page.fill("#favorite-channel-input", "Demo Channel")
    # The hidden field gets filled by jQuery UI normally; we set it manually
    page.evaluate("document.getElementById('favorite-channel-id').value = 'chan1'")
    page.click("#add-favorite-btn")

    # Wait for the reload triggered by AJAX success
    page.wait_for_load_state("networkidle")

    # Go to the /favorites page (lists favorites independently of live status)
    page.goto(f"{live_server_url}/favorites", wait_until="domcontentloaded")

    fav_selector = 'li[data-channel-id="chan1"]'
    page.wait_for_selector(fav_selector, state="visible")
    assert page.locator(fav_selector).is_visible()

    # Remove the favorite
    page.click(f"{fav_selector} .remove-favorite-btn")
    page.wait_for_selector(fav_selector, state="detached")
