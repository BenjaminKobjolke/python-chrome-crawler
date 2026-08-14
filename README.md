# python-chrome-crawler

Selenium Chrome crawler that returns rendered page HTML. Extracted from
ai-chat-data-server's `ChromeWebCrawler`, generalized for reuse.

- Bundled extensions (Manifest V3): "I still don't care about cookies" (auto-dismisses
  consent banners, e.g. Google's consent wall) and uBlock Origin Lite.
  Details: [docs/EXTENSIONS.md](docs/EXTENSIONS.md).
- Selenium Manager auto-downloads the matching chromedriver (no manual exe needed);
  an explicit `driver_path` is still supported.
- Runs Chrome for Testing by default (`browser_version="stable"`, auto-downloaded and
  cached by Selenium Manager) — regular Chrome 137+ refuses chromedriver-installed
  extensions. Set `browser_version=None` to use the installed Chrome (extensions
  won't load there).
- Settle wait after each page load so extensions can dismiss popups.
- Retry-once on a dead driver session.

## Requirements

- Python >= 3.11
- Google Chrome installed

## Installation

As a dependency in another project:

```bash
uv add "git+https://github.com/BenjaminKobjolke/python-chrome-crawler.git"
```

For local development, clone the repo and run:

```bat
install.bat
```

This runs `uv sync` (creates `.venv`, installs dependencies) and then
`tools\update_extensions.bat` to download the latest bundled extensions.

## Usage

```python
from chrome_crawler import ChromeCrawler, ChromeCrawlerConfig

config = ChromeCrawlerConfig()  # headed Chrome, bundled extensions, auto chromedriver
with ChromeCrawler(config) as crawler:
    html = crawler.get_html("https://www.google.de/search?q=test")
```

Config options: `driver_path` (empty = Selenium Manager), `headless` (`--headless=new`),
`window_size`, `use_bundled_extensions`, `extra_extensions`, `proxy` (`--proxy-server`
value — Chrome ignores embedded `user:pass` credentials), `settle_seconds`.

## Tests

```bash
uv run pytest
```

## Dependencies

- selenium >= 4.20
