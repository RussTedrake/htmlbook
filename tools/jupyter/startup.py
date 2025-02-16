import sys
import warnings

from pydrake.common.deprecation import DrakeDeprecationWarning

warnings.simplefilter("error", DrakeDeprecationWarning)

# This attempts to address a long-running issue with matplotlib and bazel,
# documented here:
# https://github.com/RobotLocomotion/drake/issues/14250#issuecomment-984217002
# The fundamental issue is that apt install python3-matplotlib creates a file
# /usr/lib/python3/dist-packages/matplotlib-3.5.1-nspkg.pth which runs at
# startup and injects the (global) path to mpl_toolkits on startup. This is
# only needed for 3d matplotlib plots; if we remove those examples we could
# remove this extra logic.

# Remove mpl_toolkits if it was loaded from system path
if "mpl_toolkits" in sys.modules:
    if "/usr/lib/python" in sys.modules["mpl_toolkits"].__file__:
        del sys.modules["mpl_toolkits"]
        # Also remove any submodules that might have been loaded
        for k in list(sys.modules.keys()):
            if k.startswith("mpl_toolkits."):
                del sys.modules[k]
