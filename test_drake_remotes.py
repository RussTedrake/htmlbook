"""Tests for prefetching Drake remote packages and the offline CI policy."""

import hashlib
import os
import subprocess
import sys
import zipfile

import pytest
from htmlbook.drake_remotes import prefetch_remotes


class FakePackageMap:
    def __init__(self, failures):
        self.failures = dict(failures)
        self.calls = []

    def GetPath(self, name):
        self.calls.append(name)
        if self.failures.get(name, 0) > 0:
            self.failures[name] -= 1
            raise RuntimeError(f"{name}: The read operation timed out")
        return f"/cache/{name}"


def test_prefetch_retries_transient_failures():
    packages = FakePackageMap({"spot_description": 2})
    delays = []
    paths = prefetch_remotes(
        packages, ["drake_models", "spot_description"], sleep=delays.append
    )
    assert paths == {
        "drake_models": "/cache/drake_models",
        "spot_description": "/cache/spot_description",
    }
    assert packages.calls == ["drake_models"] + ["spot_description"] * 3
    assert delays == [5, 10]


def test_prefetch_raises_after_last_attempt():
    packages = FakePackageMap({"spot_description": 3})
    with pytest.raises(RuntimeError, match="timed out"):
        prefetch_remotes(packages, ["spot_description"], sleep=lambda _: None)
    assert packages.calls == ["spot_description"] * 3


def test_remote_cache_without_network(tmp_path):
    """Check the CI download policy in fresh processes, as notebook tests use."""
    pytest.importorskip("pydrake")
    archive = tmp_path / "model.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("model/asset.txt", "cached model")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    env = os.environ.copy()
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    (tmp_path / "cache").mkdir()
    env["DRAKE_ALLOW_NETWORK"] = "lcm:meshcat"

    def resolve(url):
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path\n"
                "from pydrake.multibody.parsing import PackageMap\n"
                "packages = PackageMap.MakeEmpty()\n"
                "packages.AddRemote('test_model', PackageMap.RemoteParams(\n"
                f"    urls=[{url!r}], sha256={checksum!r}, strip_prefix='model'))\n"
                "asset = Path(packages.GetPath('test_model')) / 'asset.txt'\n"
                "assert asset.read_text() == 'cached model'\n",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    # An HTTPS-only package must fail immediately when the cache is empty.
    remote_url = "https://example.invalid/model.zip"
    missing = resolve(remote_url)
    assert missing.returncode != 0
    assert "DRAKE_ALLOW_NETWORK" in missing.stderr
    assert "test_model" in missing.stderr

    # Seed the real Drake cache without requiring internet access in this test.
    prefetched = resolve(archive.as_uri())
    assert prefetched.returncode == 0, prefetched.stderr
    archive.unlink()

    # A separate process can resolve the HTTPS-only package from that cache.
    cached = resolve(remote_url)
    assert cached.returncode == 0, cached.stderr
