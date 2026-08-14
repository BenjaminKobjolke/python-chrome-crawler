"""Offline checks for the build-hook download pipeline (no network)."""

import io
import json
import zipfile

import pytest

import hatch_build


def _zip_with_manifest(version: int) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("manifest.json", json.dumps({"manifest_version": version}))
    return buffer.getvalue()


def test_manifest_version_reads_plain_zip() -> None:
    assert hatch_build.manifest_version(_zip_with_manifest(3)) == 3


def test_manifest_version_skips_crx_header() -> None:
    # crx files prefix the zip payload with a binary header
    assert hatch_build.manifest_version(b"Cr24\x00\x01" + _zip_with_manifest(2)) == 2


def test_save_rejects_mv2(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(hatch_build, "fetch", lambda url: _zip_with_manifest(2))
    with pytest.raises(RuntimeError, match="MV2"):
        hatch_build.save(tmp_path, "ublock.crx", "http://example.invalid")
    assert not (tmp_path / "ublock.crx").exists()


def test_download_extensions_skips_when_present(tmp_path, monkeypatch) -> None:
    for name in hatch_build.EXTENSION_NAMES:
        (tmp_path / name).write_bytes(b"stub")
    monkeypatch.setattr(hatch_build, "fetch", lambda url: (_ for _ in ()).throw(AssertionError("network hit")))
    hatch_build.download_extensions(tmp_path)  # must not fetch
