import os

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-helusers",
    version="0.13.3",
    packages=["helusers"],
    include_package_data=True,
    license="BSD License",
    description="Django app for the user infrastructure of the City of Helsinki",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/City-of-Helsinki/django-helusers",
    author="City of Helsinki",
    author_email="dev@hel.fi",
    install_requires=[
        "Django>=4.2",
        "cachetools>=3.0.0",
        "deprecation>=2",
        "requests",
        "python-jose",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
