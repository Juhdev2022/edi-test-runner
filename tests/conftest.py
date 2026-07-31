from collections.abc import Iterator

import pytest
from playwright.sync_api import Browser, Page, sync_playwright


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    page = browser.new_page()
    yield page
    page.close()
