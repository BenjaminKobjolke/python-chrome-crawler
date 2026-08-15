"""Open the crawler's Chrome manually to check extensions or log into sites."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from chrome_crawler import ChromeCrawler, ChromeCrawlerConfig

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url", nargs="?", default="https://www.spiegel.de", help="page to open")
parser.add_argument(
    "--user-data-dir", default="",
    help="persistent profile dir (resolved to absolute); logins/cookies survive for "
         "any crawler using the same dir. empty = ephemeral profile",
)
args = parser.parse_args()

user_data_dir = str(Path(args.user_data_dir).resolve()) if args.user_data_dir else ""

with ChromeCrawler(ChromeCrawlerConfig(user_data_dir=user_data_dir)) as crawler:
    crawler.get_html(args.url)
    input("Browser open. Check the page or log in. Press Enter to close...")
