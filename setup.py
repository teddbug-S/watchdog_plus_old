from setuptools import setup

# dependencies
requires = ["watchdog"]

description = """
WatchdogPlus is a python package built on top of with more functionality built on top of the
original watchdog project. Functionality includes easy and fast api for scheduling and running.
Multiple observers on different paths at the same time
"""

setup(
    name="WatchdogPlus",
    version="1.0.2",
    author="Divine Darkey (teddbug-S)",
    author_email="teddug47@gmail.com",
    maintainer="Divine Darkey",
    maintainer_email="teddbug47@gmail.com",
    requires=requires,
    description=description
)
