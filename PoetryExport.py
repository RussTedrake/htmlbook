#! /usr/bin/env python3

import os
import subprocess
import tempfile

from packaging.markers import Marker
from pip_requirements_parser import RequirementsFile


def export_requirements():
    # Export requirements from poetry
    subprocess.run(
        ["poetry", "export", "--without-hashes", "--with", "dev", "--all-extras"],
        stdout=open("requirements.txt", "w"),
        check=True,
    )
    return RequirementsFile.from_file("requirements.txt").requirements


def remove_poetry_dependencies(requirements):
    return [req for req in requirements if not req.name.startswith("poetry")]


def modify_torch_requirements(requirements):
    modified_reqs = []
    find_links_added = False
    torch_packages = {"torch", "torchvision"}

    for req in requirements:
        print(f"Processing requirement: {req.name} {req.specifier}")  # Debug print
        if req.name in torch_packages:
            if not find_links_added:
                modified_reqs.append(
                    f"--find-links https://download.pytorch.org/whl/torch_stable.html"
                )
                find_links_added = True
            version = str(req.specifier).replace("==", "")
            # Base requirement without platform
            base_req = f"{req.name}=={version}"
            # Mac version - append platform requirement
            mac_req = (
                f'{base_req} ; {req.marker} and sys_platform == "darwin"'
                if req.marker
                else f'{base_req} ; sys_platform == "darwin"'
            )
            # Linux version - append +cpu and platform requirement
            linux_req = (
                f'{req.name}=={version}+cpu ; {req.marker} and sys_platform == "linux"'
                if req.marker
                else f'{req.name}=={version}+cpu ; sys_platform == "linux"'
            )
            modified_reqs.append(mac_req)
            modified_reqs.append(linux_req)
        else:
            modified_reqs.append(req.line)

    # Write to temporary file and parse again to get InstallRequirement objects
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    try:
        with temp_file as f:
            for req in modified_reqs:
                f.write(req + "\n")
        return RequirementsFile.from_file(temp_file.name).requirements
    finally:
        os.unlink(temp_file.name)  # Clean up the temporary file


def should_include_for_platform(requirement, platform):
    if not requirement.marker:
        return True

    # Create contexts for evaluation
    mac_context = {"sys_platform": "darwin"}
    linux_context = {"sys_platform": "linux"}

    context = mac_context if platform == "darwin" else linux_context
    return Marker(str(requirement.marker)).evaluate(context)


def write_platform_requirements(requirements):
    with open("requirements-bazel.txt", "w") as f_bazel, open(
        "requirements-bazel-mac.txt", "w"
    ) as f_mac, open("requirements-bazel-linux.txt", "w") as f_linux:
        for req in requirements:
            f_bazel.write(req.line + "\n")
            if should_include_for_platform(req, "darwin"):
                f_mac.write(req.line + "\n")
            if should_include_for_platform(req, "linux"):
                f_linux.write(req.line + "\n")


def main():
    # Export from poetry and load.
    reqs = export_requirements()

    # Make some changes for bazel compatibility.
    reqs = remove_poetry_dependencies(reqs)
    reqs = modify_torch_requirements(reqs)

    # Write final platform-specific files
    write_platform_requirements(reqs)


if __name__ == "__main__":
    main()
