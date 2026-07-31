from pathlib import Path

from playwright.sync_api import Page

REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"


def test_abre_site_publico_e_tira_screenshot(page: Page) -> None:
    page.goto("https://playwright.dev/")

    assert "Playwright" in page.title()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshot_path = REPORTS_DIR / "smoke_playwright_dev.png"
    page.screenshot(path=str(screenshot_path))

    assert screenshot_path.exists()
