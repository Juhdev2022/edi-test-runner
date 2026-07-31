import functools
import http.server
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

MOCKS_EDI_DIR = Path(__file__).resolve().parent / "mocks" / "edi"


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


@pytest.fixture(scope="session")
def edi_mock_url() -> Iterator[str]:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(MOCKS_EDI_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # server_address é tipado genericamente pelo stdlib (pode ser IPv4/IPv6/unix
    # socket); como o bind acima é sempre IPv4, o cast documenta essa garantia.
    host, port = cast(tuple[str, int], server.server_address)
    yield f"http://{host}:{port}"

    server.shutdown()
    server.server_close()
    thread.join()
