def vtk_test_tags():
    """Returns test tags necessary for properly running VTK rendering tests
    locally.
    """
    return [
        # Defects related to platform-specific rendering-related libraries
        # when run under DRD or Helgrind.
        "no_drd",
        "no_helgrind",
        # Disable under LeakSanitizer and Valgrind Memcheck due to
        # driver-related leaks. For more information, see #7520.
        "no_lsan",
        "no_memcheck",
        # Mitigates driver-related issues when running under `bazel test`. For
        # more information, see #7004.
        "no-sandbox",
    ]
