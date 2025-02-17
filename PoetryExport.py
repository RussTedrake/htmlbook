#! /usr/bin/env python3

import os
import subprocess
import tempfile

from packaging.markers import Marker
from pip_requirements_parser import RequirementsFile, build_install_req, RequirementLine


def export_requirements():
    # Export requirements from poetry
    subprocess.run(
        ["poetry", "export", "--without-hashes", "--with", "dev", "--all-extras"],
        stdout=open("requirements.txt", "w"),
        check=True,
    )
    # Add PyTorch find-links option
    with open("requirements.txt", "r") as f:
        content = f.read()
    with open("requirements.txt", "w") as f:
        f.write("--find-links https://download.pytorch.org/whl/torch_stable.html\n")
        f.write(content)
    return RequirementsFile.from_file("requirements.txt")


def remove_poetry_dependencies(requirements_file):
    requirements_file.requirements = [
        req for req in requirements_file.requirements if not req.name.startswith("poetry")
    ]
    return requirements_file


def modify_torch_requirements(requirements_file):
    torch_packages = {"torch", "torchvision"}
    
    modified_requirements = []
    
    for req in requirements_file.requirements:
        if req.name in torch_packages:
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
            # Parse the new requirements into Requirement objects
            modified_requirements.append(build_install_req(mac_req, RequirementLine(line=mac_req)))
            modified_requirements.append(build_install_req(linux_req, RequirementLine(line=linux_req)))
        else:
            modified_requirements.append(req)
    
    requirements_file.requirements = modified_requirements
    return requirements_file


def should_include_for_platform(requirement, platform):
    if not requirement.marker:
        return True

    # Create contexts for evaluation
    mac_context = {"sys_platform": "darwin"}
    linux_context = {"sys_platform": "linux"}

    context = mac_context if platform == "darwin" else linux_context
    return Marker(str(requirement.marker)).evaluate(context)


def write_platform_requirements(requirements_file):
    with open("requirements-bazel.txt", "w") as f_bazel, open(
        "requirements-bazel-mac.txt", "w"
    ) as f_mac, open("requirements-bazel-linux.txt", "w") as f_linux:
        for file in [f_bazel, f_mac, f_linux]:
            for option in requirements_file.options:
                file.write(option.requirement_line.line + "\n")
        for req in requirements_file.requirements:
            f_bazel.write(req.requirement_line.line + "\n")
            if should_include_for_platform(req, "darwin"):
                f_mac.write(req.requirement_line.line + "\n")
            if should_include_for_platform(req, "linux"):
                f_linux.write(req.requirement_line.line + "\n")


def main():
    # Export from poetry and load.
    requirements_file = export_requirements()

    # Make some changes for bazel compatibility.
    requirements_file = remove_poetry_dependencies(requirements_file)
    requirements_file = modify_torch_requirements(requirements_file)

    # Write final platform-specific files
    write_platform_requirements(requirements_file)


if __name__ == "__main__":
    main()
