# Steps for doing a release

**Note!** Releases are handled by GitHub Actions. This document is for reference only.

## Preparation

Update changelog.

Bump version number in `setup.py`.

Commit, push and merge the above changes.

## Building the release package

Make sure `wheel` is installed.

Run:

```bash
python setup.py sdist bdist_wheel
```

## Uploading release to PyPI

This step requires an account on PyPI (and TestPyPI) and needed privileges for the project there.

Make sure `twine` is installed.

Upload to Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

Upload to main PyPI:

```bash
python -m twine upload dist/*
```

## References:

- https://packaging.python.org/tutorials/packaging-projects/
- https://packaging.python.org/guides/using-testpypi/
- https://packaging.python.org/specifications/pypirc/#using-a-pypi-token
- https://test.pypi.org
- https://pypi.org
