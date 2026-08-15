# Browser profiles

## How `user_data_dir` works

`ChromeCrawlerConfig.user_data_dir` controls the Chrome profile the crawler runs in:

- **Empty (default):** Chrome creates a fresh, ephemeral profile per launch. Nothing
  survives `quit()` — no cookies, no consent choices, no logins. Sites see a cold
  first-time browser every run, which raises bot-detection/captcha odds.
- **Set to a directory path:** passed to Chrome as `--user-data-dir`. The directory is
  created on first launch and reused afterwards; cookies, consent decisions and logins
  persist across runs. Use an **absolute** path — Chrome misbehaves with relative
  `--user-data-dir` values (it resolves them against Chrome's own working directory,
  not yours).

The value is the *user data root* (Chrome creates a `Default` profile inside it), not a
single profile subfolder.

## Recommended pattern: dedicated profile + manual login

Give each project its own profile directory and, if a Google/site login helps, perform
that login manually **through the crawler itself** (same binary, same profile):

```python
with ChromeCrawler(ChromeCrawlerConfig(user_data_dir=r"D:\myproject\chrome-profile")) as crawler:
    crawler.get_html("https://www.google.com")
    input("Log in in the Chrome window, then press Enter to close...")
```

Every later crawl with the same `user_data_dir` reuses that session. If a site flags the
profile, delete the directory to start fresh.

## Why pointing at a real branded-Chrome profile mostly fails

Setting `user_data_dir` to an installed Chrome's profile
(`C:\Users\<you>\AppData\Local\Google\Chrome\User Data`) is possible but has three traps:

1. **Profile lock.** Chrome allows one running instance per user data directory. If the
   user's Chrome is open, the crawler fails with
   "user data directory is already in use". Chrome must be fully closed first.
2. **Version mismatch.** The crawler defaults to Chrome for Testing
   (`browser_version="stable"`, see `docs/EXTENSIONS.md`), which may be older than the
   installed branded Chrome. Chrome refuses to open profiles created by a newer version
   ("profile was created by a newer version of Chrome").
3. **App-bound cookie encryption (Chrome 127+).** Branded Chrome encrypts cookies so that
   only the exact binary that wrote them can decrypt them. Chrome for Testing is a
   different binary: it can open the profile but **cannot read the existing login
   cookies** — the user appears logged out even though the profile "has" the session.
   Logins therefore do not transfer from branded Chrome; they must be created inside the
   crawler's own browser (pattern above).

## Extensions and persistent profiles

Bundled `.crx` extensions are installed by chromedriver on every launch, so they are
present in persistent profiles too. The generated proxy-auth extension
(`--load-extension`, see `crawler.py`) lives in the OS temp dir and is re-generated per
launch — it does not accumulate in the profile.
