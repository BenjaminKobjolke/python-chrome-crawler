"""Hatchling build hook: download bundled extensions at wheel-build time.

Consumers install this library from git, so uv/pip build the wheel on their
machine and this hook runs there — the closest thing to a post-install step
Python packaging allows. The .crx files are gitignored; `artifacts` in
pyproject.toml force-includes them in the wheel.

- cookies.crx: I Still Don't Care About Cookies — the release ships a plain zip
  (ISDCAC-chrome-source.zip); renaming it to .crx is enough for add_extension().
- ublock.crx: uBlock Origin Lite (MV3) straight from the Chrome Web Store crx
  endpoint. Full uBlock Origin is MV2 and no Chrome build loads MV2 anymore.

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
UBLOCK_URL = (
    "https://clients2.google.com/service/update2/crx"
    "?response=redirect&prodversion=152.0&acceptformat=crx3"
    "&x=id%3Dddkjiahejlhfcafbddmgiahcphecmpfh%26uc"  # uBlock Origin Lite
)


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "chrome-crawler-updater"})) as resp:
        return resp.read()


def manifest_version(data: bytes) -> int:
    z = zipfile.ZipFile(io.BytesIO(data[data.find(b"PK\x03\x04"):]))
    return json.loads(z.read("manifest.json"))["manifest_version"]


def save(target_dir: Path, name: str, url: str) -> None:
    data = fetch(url)
    mv = manifest_version(data)
    if mv != 3:
        raise RuntimeError(f"{name} is MV{mv} — Chrome only loads MV3, refusing to bundle")
    target = target_dir / name
    target.write_bytes(data)
    print(f"{name}: {len(data)} bytes, manifest_version {mv}, from {url}")


def download_extensions(target_dir: Path, force: bool = False) -> None:
    """Download both .crx into target_dir. Skips when all present unless force."""
    if not force and all((target_dir / name).exists() for name in EXTENSION_NAMES):
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    save(target_dir, "cookies.crx", ISDCAC_URL)
    save(target_dir, "ublock.crx", UBLOCK_URL)


class DownloadExtensionsHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        try:
            download_extensions(EXTENSIONS_DIR)
        except Exception as error:
            raise RuntimeError(
                "python-chrome-crawler: could not download bundled extensions "
                f"({error}) — check network access; see docs/EXTENSIONS.md"
            ) from error
