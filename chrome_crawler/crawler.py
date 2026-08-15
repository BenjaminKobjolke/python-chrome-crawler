"""Chrome driver lifecycle and rendered-HTML fetching.

Extracted from ai-chat-data-server's ChromeWebCrawler: headed Chrome with the
bundled "I still don't care about cookies" (consent auto-dismiss) and uBlock
Origin extensions, a settle wait after page load, and
retry-once on a dead driver.
"""
from __future__ import annotations

import json
import logging
import tempfile
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
    proxy: str | None = None  # --proxy-server value (scheme://host:port, no credentials)
    # --proxy-server ignores user:pass (and Selenium's BiDi continueWithAuth times out on
    # proxy 407s), so credentials are answered by a generated MV3 extension instead.
    proxy_user: str = ""
    proxy_password: str = ""
    settle_seconds: float = 3.0  # let extensions dismiss consent/popups after load
    # Persistent Chrome profile directory (--user-data-dir); cookies/consent survive runs,
    # which sites treat as less bot-like. Empty = fresh ephemeral profile per launch.
    user_data_dir: str = ""
    # Chrome 137+ branded builds refuse chromedriver's extension install, so default to
    # Chrome for Testing (Selenium Manager downloads + caches it). None = installed Chrome.
    browser_version: str | None = "stable"


def build_options(config: ChromeCrawlerConfig) -> Options:
    options = Options()
    options.add_argument(f"--window-size={config.window_size}")
    # Without these, Google serves a reCAPTCHA page to Selenium-driven Chrome
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if config.browser_version:
        options.browser_version = config.browser_version
    if config.headless:
        options.add_argument("--headless=new")
    if config.user_data_dir:
        options.add_argument(f"--user-data-dir={config.user_data_dir}")
    if config.proxy:
        options.add_argument(f"--proxy-server={config.proxy}")
        if config.proxy_user:
            # --load-extension needs an unpacked dir; branded Chrome 137+ refuses it, but
            # the default browser_version="stable" runs Chrome for Testing, which allows it.
            auth_extension = _write_proxy_auth_extension(config.proxy_user, config.proxy_password)
            options.add_argument(f"--load-extension={auth_extension}")
    for extension in extension_paths(config):
        options.add_extension(extension)
    return options


def _write_proxy_auth_extension(user: str, password: str) -> str:
    """Write an unpacked MV3 extension that answers (proxy) auth challenges.

    Credentials land in a plain file under the OS temp dir for the browser's lifetime.
    """
    directory = Path(tempfile.mkdtemp(prefix="chrome_crawler_proxy_auth_"))
    manifest = {
        "name": "Proxy Auth",
        "version": "1.0",
        "manifest_version": 3,
        "permissions": ["webRequest", "webRequestAuthProvider"],
        "host_permissions": ["<all_urls>"],
        "background": {"service_worker": "background.js"},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    credentials = json.dumps({"username": user, "password": password})
    (directory / "background.js").write_text(
        "chrome.webRequest.onAuthRequired.addListener(\n"
        f"  (details, callback) => {{ callback({{authCredentials: {credentials}}}); }},\n"
        '  {urls: ["<all_urls>"]},\n'
        '  ["asyncBlocking"]\n'
        ");\n",
        encoding="utf-8",
    )
    return str(directory)


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

    def current_html(self) -> str:
        """Re-read the current page without navigating (for JS-still-rendering polls)."""
        return self._ensure_driver().page_source

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
            self._driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
            )
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
