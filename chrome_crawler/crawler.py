"""Chrome driver lifecycle and rendered-HTML fetching.

Extracted from ai-chat-data-server's ChromeWebCrawler: headed Chrome with the
bundled "I don't care about cookies" (consent auto-dismiss) and uBlock Origin
extensions, a settle wait after page load, and retry-once on a dead driver.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from types import TracebackType

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

_EXTENSIONS_DIR = Path(__file__).parent / "extensions"
_logger = logging.getLogger("chrome_crawler")


@dataclass(frozen=True)
class ChromeCrawlerConfig:
    driver_path: str = ""  # empty = Selenium Manager downloads the matching chromedriver
    headless: bool = False  # --headless=new supports extensions, unlike legacy headless
    window_size: str = "1024,720"
    use_bundled_extensions: bool = True  # cookies.crx (consent dismiss) + ublock.crx
    extra_extensions: tuple[str, ...] = ()
    proxy: str | None = None  # --proxy-server value; Chrome ignores user:pass credentials
    settle_seconds: float = 3.0  # let extensions dismiss consent/popups after load


def build_options(config: ChromeCrawlerConfig) -> Options:
    options = Options()
    options.add_argument(f"--window-size={config.window_size}")
    if config.headless:
        options.add_argument("--headless=new")
    if config.proxy:
        options.add_argument(f"--proxy-server={config.proxy}")
    for extension in extension_paths(config):
        options.add_extension(extension)
    return options


def extension_paths(config: ChromeCrawlerConfig) -> list[str]:
    paths: list[str] = []
    if config.use_bundled_extensions:
        paths.extend(str(path) for path in sorted(_EXTENSIONS_DIR.glob("*.crx")))
    paths.extend(config.extra_extensions)
    return paths


class ChromeCrawler:
    """Reuses one Chrome driver across get_html calls. Use as a context manager."""

    def __init__(self, config: ChromeCrawlerConfig) -> None:
        self._config = config
        self._driver: webdriver.Chrome | None = None

    def get_html(self, url: str) -> str:
        driver = self._ensure_driver()
        try:
            driver.get(url)
        except Exception as error:  # noqa: BLE001 - dead driver/session: recreate once
            _logger.warning("Page load failed, restarting driver: %s", error)
            self.quit()
            driver = self._ensure_driver()
            driver.get(url)
        sleep(self._config.settle_seconds)
        return driver.page_source

    def quit(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception as error:  # noqa: BLE001 - already-dead driver is fine
                _logger.debug("Driver quit failed: %s", error)
            self._driver = None

    def _ensure_driver(self) -> webdriver.Chrome:
        if self._driver is None:
            service = Service(self._config.driver_path) if self._config.driver_path else Service()
            self._driver = webdriver.Chrome(options=build_options(self._config), service=service)
        return self._driver

    def __enter__(self) -> ChromeCrawler:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.quit()
