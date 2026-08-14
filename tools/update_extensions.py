"""Download the latest bundled extensions from GitHub releases.

- cookies.crx: I Still Don't Care About Cookies — the release ships a plain zip
  (ISDCAC-chrome-source.zip); renaming it to .crx is enough for add_extension().
- ublock.crx: uBlock Origin packed as crx by imputnet/ublock-origin-crx.
"""

import io
import json
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

EXTENSIONS_DIR = Path(__file__).parent.parent / "chrome_crawler" / "extensions"

ISDCAC_URL = (
    "https://github.com/OhMyGuus/I-Still-Dont-Care-About-Cookies"
    "/releases/latest/download/ISDCAC-chrome-source.zip"
)
UBLOCK_API = "https://api.github.com/repos/imputnet/ublock-origin-crx/releases/latest"


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "chrome-crawler-updater"})) as resp:
        return resp.read()


def manifest_version(data: bytes) -> int:
    z = zipfile.ZipFile(io.BytesIO(data[data.find(b"PK\x03\x04"):]))
    return json.loads(z.read("manifest.json"))["manifest_version"]


def save(name: str, url: str) -> None:
    data = fetch(url)
    mv = manifest_version(data)
    target = EXTENSIONS_DIR / name
    target.write_bytes(data)
    print(f"{name}: {len(data)} bytes, manifest_version {mv}, from {url}")
    if mv != 3:
        print(f"  warning: {name} is MV{mv} — verify it loads via tools\\open_browser.bat")


def main() -> int:
    save("cookies.crx", ISDCAC_URL)
    release = json.loads(fetch(UBLOCK_API))
    save("ublock.crx", release["assets"][0]["browser_download_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
