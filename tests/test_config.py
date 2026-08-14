"""Unit tests for option building — no browser started."""
from chrome_crawler.crawler import ChromeCrawlerConfig, build_options, extension_paths


def test_default_options_headed_with_bundled_extensions() -> None:
    config = ChromeCrawlerConfig()
    options = build_options(config)
    assert "--window-size=1024,720" in options.arguments
    assert "--headless=new" not in options.arguments
    assert not any(arg.startswith("--proxy-server") for arg in options.arguments)
    assert len(options.extensions) == 2  # cookies.crx + ublock.crx


def test_headless_proxy_and_extra_extension_flags() -> None:
    config = ChromeCrawlerConfig(headless=True, proxy="http://proxy.example.com:8080",
                                 use_bundled_extensions=False)
    options = build_options(config)
    assert "--headless=new" in options.arguments
    assert "--proxy-server=http://proxy.example.com:8080" in options.arguments
    assert options.extensions == []


def test_proxy_credentials_load_auth_extension() -> None:
    import json
    from pathlib import Path

    config = ChromeCrawlerConfig(proxy="http://proxy.example.com:8080",
                                 proxy_user="alice", proxy_password="secret",
                                 use_bundled_extensions=False)
    options = build_options(config)
    assert "--proxy-server=http://proxy.example.com:8080" in options.arguments
    load_args = [arg for arg in options.arguments if arg.startswith("--load-extension=")]
    assert len(load_args) == 1
    extension_dir = Path(load_args[0].split("=", 1)[1])
    manifest = json.loads((extension_dir / "manifest.json").read_text())
    assert "webRequestAuthProvider" in manifest["permissions"]
    background = (extension_dir / "background.js").read_text()
    assert '"alice"' in background
    assert '"secret"' in background


def test_proxy_without_credentials_loads_no_auth_extension() -> None:
    config = ChromeCrawlerConfig(proxy="http://proxy.example.com:8080",
                                 use_bundled_extensions=False)
    options = build_options(config)
    assert not any(arg.startswith("--load-extension") for arg in options.arguments)


def test_extension_paths_bundled_sorted() -> None:
    paths = extension_paths(ChromeCrawlerConfig())
    names = [path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1] for path in paths]
    assert names == ["cookies.crx", "ublock.crx"]
