"""Unit tests for ChromeCrawler driver interaction — driver stubbed, no browser."""
from unittest.mock import MagicMock, patch

from chrome_crawler import ChromeCrawler, ChromeCrawlerConfig


def test_ensure_driver_registers_proxy_auth_handler() -> None:
    config = ChromeCrawlerConfig(proxy="http://proxy.example.com:8080",
                                 proxy_user="alice", proxy_password="secret")
    crawler = ChromeCrawler(config)
    driver = MagicMock()
    with patch("chrome_crawler.crawler.webdriver.Chrome", return_value=driver):
        crawler._ensure_driver()
    driver.network.add_auth_handler.assert_called_once_with("alice", "secret")


def test_ensure_driver_skips_auth_handler_without_credentials() -> None:
    crawler = ChromeCrawler(ChromeCrawlerConfig(proxy="http://proxy.example.com:8080"))
    driver = MagicMock()
    with patch("chrome_crawler.crawler.webdriver.Chrome", return_value=driver):
        crawler._ensure_driver()
    driver.network.add_auth_handler.assert_not_called()


def test_current_html_returns_driver_page_source_without_navigating() -> None:
    crawler = ChromeCrawler(ChromeCrawlerConfig())
    driver = MagicMock()
    driver.page_source = "<html>still rendering</html>"
    with patch.object(crawler, "_ensure_driver", return_value=driver):
        assert crawler.current_html() == "<html>still rendering</html>"
    driver.get.assert_not_called()
