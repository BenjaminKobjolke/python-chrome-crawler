"""Open the crawler's Chrome manually to check the bundled extensions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chrome_crawler import ChromeCrawler, ChromeCrawlerConfig

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.spiegel.de"

with ChromeCrawler(ChromeCrawlerConfig()) as crawler:
    crawler.get_html(url)
    input("Browser open. Check chrome://extensions or the page. Press Enter to close...")
