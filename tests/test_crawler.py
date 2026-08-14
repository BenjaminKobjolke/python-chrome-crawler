"""Unit tests for ChromeCrawler driver interaction — driver stubbed, no browser."""
from unittest.mock import MagicMock, patch

from chrome_crawler import ChromeCrawler, ChromeCrawlerConfig


def test_current_html_returns_driver_page_source_without_navigating() -> None:
    crawler = ChromeCrawler(ChromeCrawlerConfig())
    driver = MagicMock()
    driver.page_source = "<html>still rendering</html>"
    with patch.object(crawler, "_ensure_driver", return_value=driver):
        assert crawler.current_html() == "<html>still rendering</html>"
    driver.get.assert_not_called()
