# Browser extensions

## What is bundled

`chrome_crawler/extensions/` ships two Chrome Web Store extensions as `.crx` files:

| File | Extension | Purpose |
|---|---|---|
| `cookies.crx` | I still don't care about cookies (MV3) | Auto-dismisses cookie/consent banners (e.g. Google's consent wall) |
| `ublock.crx` | uBlock Origin Lite (MV3) | Blocks ads so pages settle faster and HTML is cleaner |

## How they are loaded

- `extension_paths()` in `chrome_crawler/crawler.py` globs **all** `*.crx` in that
  folder (filenames don't matter) plus anything in `ChromeCrawlerConfig.extra_extensions`.
- Each path is passed to Selenium's `options.add_extension()`; chromedriver installs
  them into the temporary browser profile at launch.
- `use_bundled_extensions=False` disables the bundled ones.
- After each page load the crawler waits `settle_seconds` (default 3s) so the
  extensions can dismiss popups before `page_source` is read.

## Why extensions broke (and the fix)

Two independent Chrome changes killed the original setup:

1. **Chrome 137+ (branded builds) refuses chromedriver-installed extensions.**
   The `--load-extension` mechanism chromedriver uses is ignored by regular
   Google Chrome. Verified on Chrome 150: zero extensions installed, silently.
2. **Manifest V2 removed in Chrome ~139.** The old bundled uBlock Origin (full)
   and "I don't care about cookies" were MV2 — refused by regular Chrome.
   Chrome for Testing 150 was more lenient and still loaded the full uBlock
   Origin MV2 crx (tested 2026-08-14).
3. **Chrome for Testing 152 dropped MV2 too** ("unsupported manifest version"
   dialog at launch). The `ExtensionManifestV2Availability` enterprise policy
   was removed in Chrome 139 — there is no flag or setting to re-enable MV2
   anywhere. So `ublock.crx` is now uBlock Origin Lite (MV3); the build hook
   refuses to bundle anything that isn't MV3.

Fix (both parts required):

- **Run Chrome for Testing instead of installed Chrome.**
  `ChromeCrawlerConfig.browser_version = "stable"` (the default) makes Selenium
  Manager download and cache the Chrome for Testing binary (~150MB, one-time,
  cached under `~/.cache/selenium`). This non-branded build still allows
  chromedriver extension installs. `browser_version=None` uses the installed
  Chrome — extensions will NOT load there.
- **Ship MV3 extensions.** "I don't care about cookies" →
  "I still don't care about cookies" (MV3); uBlock Origin full (MV2) →
  uBlock Origin Lite (MV3).

## How the .crx files get there

The `.crx` files are **not committed** (gitignored) and not stored in the repo.
A hatchling build hook (`hatch_build.py`, registered via
`[tool.hatch.build.hooks.custom]`) downloads them at wheel-build time and
`[tool.hatch.build] artifacts` force-includes them in the wheel despite the
gitignore. Consumers install from git, so uv/pip build the wheel on their
machine — plain `uv sync` downloads and bundles the extensions automatically.

- The first `uv sync` of a new library commit needs network access; the build
  fails with a clear error if the download fails. uv caches the built wheel per
  git commit, so later syncs need no network.
- The hook skips downloading when both files already exist (dev checkout).

## Updating the bundled .crx files

Run `tools\update_extensions.bat` (thin wrapper over the download logic in
`hatch_build.py`). It force-downloads the latest GitHub releases:

- `cookies.crx` ← [OhMyGuus/I-Still-Dont-Care-About-Cookies](https://github.com/OhMyGuus/I-Still-Dont-Care-About-Cookies/releases)
  (`ISDCAC-chrome-source.zip` — a plain zip; renaming it to `.crx` is enough for
  `add_extension()` with Chrome for Testing)
- `ublock.crx` ← Web Store crx endpoint for uBlock Origin Lite
  (`https://clients2.google.com/service/update2/crx?response=redirect&prodversion=152.0&acceptformat=crx3&x=id%3Dddkjiahejlhfcafbddmgiahcphecmpfh%26uc`)

The script prints each file's `manifest_version` and **errors** on anything
that isn't MV3 (no Chrome build loads MV2 anymore). The same Web Store
endpoint works for any extension by swapping the ID (I still don't care about
cookies: `edibdbjcniadpccecjdfdjjppcpchdlm`).

Check `manifest_version` inside a crx (zip payload starts after the crx header):

```python
import io, json, zipfile
data = open("ublock.crx", "rb").read()
z = zipfile.ZipFile(io.BytesIO(data[data.find(b"PK\x03\x04"):]))
print(json.loads(z.read("manifest.json"))["manifest_version"])  # must be 3
```

## Verifying extensions work

Run `tools\open_browser.bat` — opens the crawler's Chrome on spiegel.de. Expect no
cookie banner, no ads; `chrome://extensions` should list both extensions enabled.
Pass a URL as first argument to test a different site.
