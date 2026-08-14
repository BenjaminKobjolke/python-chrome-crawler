# python-chrome-crawler

Selenium Chrome crawler that returns rendered page HTML. Extracted from
ai-chat-data-server's `ChromeWebCrawler`, generalized for reuse.

- Bundled extensions: "I don't care about cookies" (auto-dismisses consent banners,
  e.g. Google's consent wall) and uBlock Origin.
- Selenium Manager auto-downloads the matching chromedriver (no manual exe needed);
  an explicit `driver_path` is still supported.
- Settle wait after each page load so extensions can dismiss popups.
- Retry-once on a dead driver session.

## Requirements

- Python >= 3.11
- Google Chrome installed

## Installation

```bash
uv add "git+https://github.com/BenjaminKobjolke/python-chrome-crawler.git"
```

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
