"""Prefetch Drake remote packages so that tests can run without downloads.

Each book's `setup/prefetch_remotes.py` registers the remote packages its tests
use on a `pydrake.multibody.parsing.PackageMap` and passes their names to
`prefetch_remotes()`. CI runs that script before pytest, with the same user,
Python, and `XDG_CACHE_HOME` as the tests, and then runs pytest with
`DRAKE_ALLOW_NETWORK=lcm:meshcat` so that an uncached package fails instead of
downloading. See Drake's network policy documentation:
https://drake.mit.edu/doxygen_cxx/group__allow__network.html
"""

import logging
import time


def prefetch_remotes(package_map, package_names, *, attempts=3, sleep=time.sleep):
    """Fetch each named package into Drake's cache, retrying failed downloads.

    `package_map` is a PackageMap on which the remote packages are already
    registered. Downloads are verified against their sha256 by Drake, so
    retrying a failed one is safe. Returns the resolved package paths.
    """
    paths = {}
    for name in package_names:
        for attempt in range(1, attempts + 1):
            print(f"fetching {name}", flush=True)
            try:
                paths[name] = package_map.GetPath(name)
                break
            except RuntimeError as error:
                if attempt == attempts:
                    raise
                delay = 2 ** (attempt - 1) * 5
                logging.warning(
                    "Fetching %s failed (attempt %d/%d): %s; retrying in %d seconds",
                    name,
                    attempt,
                    attempts,
                    error,
                    delay,
                )
                sleep(delay)
    return paths
