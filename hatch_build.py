"""Hatchling build hook: download bundled extensions at wheel-build time.

Consumers install this library from git, so uv/pip build the wheel on their
machine and this hook runs there — the closest thing to a post-install step
Python packaging allows. The .crx files are gitignored; `artifacts` in
pyproject.toml force-includes them in the wheel.

- cookies.crx: I Still Don't Care About Cookies — the release ships a plain zip
  (ISDCAC-chrome-source.zip); renaming it to .crx is enough for add_extension().
- ublock.crx: uBlock Origin packed as crx by imputnet/ublock-origin-crx.

Stdlib only: build hooks cannot pull extra dependencies without
require-runtime-dependencies gymnastics.
"""

import io
import json
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from hatchling.builders.hooks.plugin.interface import BuildHookInterface
except ModuleNotFoundError:  # tools/update_extensions.py imports us outside a build env
    BuildHookInterface = object  # type: ignore[assignment, misc]

EXTENSIONS_DIR = Path(__file__).parent / "chrome_crawler" / "extensions"
EXTENSION_NAMES = ("cookies.crx", "ublock.crx")

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


def save(target_dir: Path, name: str, url: str) -> None:
    data = fetch(url)
    mv = manifest_version(data)
    target = target_dir / name
    target.write_bytes(data)
    print(f"{name}: {len(data)} bytes, manifest_version {mv}, from {url}")
    if mv != 3:
        print(f"  warning: {name} is MV{mv} — verify it loads via tools\\open_browser.bat")


def download_extensions(target_dir: Path, force: bool = False) -> None:
    """Download both .crx into target_dir. Skips when all present unless force."""
    if not force and all((target_dir / name).exists() for name in EXTENSION_NAMES):
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    save(target_dir, "cookies.crx", ISDCAC_URL)
    release = json.loads(fetch(UBLOCK_API))
    save(target_dir, "ublock.crx", release["assets"][0]["browser_download_url"])


class DownloadExtensionsHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        try:
            download_extensions(EXTENSIONS_DIR)
        except Exception as error:
            raise RuntimeError(
                "python-chrome-crawler: could not download bundled extensions "
                f"({error}) — check network access; see docs/EXTENSIONS.md"
            ) from error
