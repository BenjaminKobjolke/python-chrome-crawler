# Browser extensions

## What is bundled

`chrome_crawler/extensions/` ships two Chrome Web Store extensions as `.crx` files:

| File | Extension | Purpose |
|---|---|---|
| `cookies.crx` | I still don't care about cookies (MV3) | Auto-dismisses cookie/consent banners (e.g. Google's consent wall) |
| `ublock.crx` | uBlock Origin (full, MV2) | Blocks ads so pages settle faster and HTML is cleaner |

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
   Chrome for Testing is more lenient: the full uBlock Origin MV2 crx from
   imputnet/ublock-origin-crx was verified loading fine there (tested 2026-08-14),
   so MV2 works for us as long as we run Chrome for Testing.

Fix (both parts required):

- **Run Chrome for Testing instead of installed Chrome.**
  `ChromeCrawlerConfig.browser_version = "stable"` (the default) makes Selenium
  Manager download and cache the Chrome for Testing binary (~150MB, one-time,
  cached under `~/.cache/selenium`). This non-branded build still allows
  chromedriver extension installs. `browser_version=None` uses the installed
  Chrome — extensions will NOT load there.
- **Ship extensions Chrome for Testing accepts.** "I don't care about cookies" →
  "I still don't care about cookies" (MV3); uBlock Origin full (MV2) still loads
  in Chrome for Testing.

## Updating the bundled .crx files

Run `tools\update_extensions.bat`. It downloads the latest GitHub releases:

- `cookies.crx` ← [OhMyGuus/I-Still-Dont-Care-About-Cookies](https://github.com/OhMyGuus/I-Still-Dont-Care-About-Cookies/releases)
  (`ISDCAC-chrome-source.zip` — a plain zip; renaming it to `.crx` is enough for
  `add_extension()` with Chrome for Testing)
- `ublock.crx` ← [imputnet/ublock-origin-crx](https://github.com/imputnet/ublock-origin-crx/releases)
  (full uBlock Origin packed as crx; MV2, but verified loading fine in Chrome for
  Testing — see note below)

The script prints each file's `manifest_version` and warns on MV2. Fallback:
the Web Store crx endpoint
`https://clients2.google.com/service/update2/crx?response=redirect&prodversion=150.0&acceptformat=crx3&x=id%3D<EXTENSION_ID>%26uc`
(IDs: uBlock Origin Lite `ddkjiahejlhfcafbddmgiahcphecmpfh`,
I still don't care about cookies `edibdbjcniadpccecjdfdjjppcpchdlm`).

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
