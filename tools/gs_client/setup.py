from setuptools import setup, find_packages

package_list = find_packages(include=["gs_client", "gs_client.*"])

setup(
    name="gs_client",
    version="0.4.0",
    setup_requires=["signalrcore"],  # gs_common is also a dependency
    description="Client to send requests to GoatSwitch AI backend",
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
)
