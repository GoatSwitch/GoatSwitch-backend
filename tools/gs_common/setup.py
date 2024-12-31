from setuptools import find_packages, setup
from setuptools.command.build_py import build_py as _build_py


class BuildPackageProtos(_build_py):
    """Command to generate project *_pb2.py modules from proto files."""

    # ...
    def run(self):
        from grpc_tools import command

        command.build_package_protos(".")
        super().run()


package_list = find_packages(include=["gs_common", "gs_common.*"])

setup(
    name="gs_common",
    version="0.8.0",
    setup_requires=["grpcio-tools==1.50.0"],
    description="Common code that is shared across all goatswitch services",
    author="GoatSwitch AI",
    author_email="hello@goatswitch.ai",
    license="MIT",
    packages=package_list,
    # these files are needed for type checking but not included by default
    package_data={
        package: ["py.typed", "*.pyi", "**/.pyi"] for package in package_list
    },
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    cmdclass={
        "build_py": BuildPackageProtos,
    },
)
