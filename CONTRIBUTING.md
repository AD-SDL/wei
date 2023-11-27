# Contributing to wei

If you are interested in contributing to wei, your contributions will fall into two categories:

1. You want to implement a new feature:
    - In general, we accept any features as long as they fit the scope of this package. If you are unsure about this or need help on the design/implementation of your feature, post about it in an issue.
2. You want to fix a bug:
    - Please post an issue using the Bug template which provides a clear and concise description of what the bug was.

Once you finish implementing a feature or bug-fix, please send a Pull Request to https://github.com/AD-SDL/wei.

## Developing wei

To develop wei on your machine, please follow these instructions:

1. Clone a copy of wei from source:

```
git clone https://github.com/AD-SDL/wei.git
cd wei
```

2. If you already have wei from source, update it:

```
git pull
```

3. Install wei in `develop` mode:

```
conda create -n rpl-wei python=3.9
conda activate rpl-wei
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```

This mode will symlink the Python files from the current local source tree into the Python install.
Hence, if you modify a Python file, you do not need to reinstall wei again and again.

4. Ensure that you have a working `wei` installation by running:

```
python3 -c "import wei; print(wei.__version__)"
```

5. To run dev tools (isort, flake8, black):

```
make
```

## Unit Testing

To run the test suite:

1. [Build and install](#developing-wei) wei from source.
2. The `requirements/dev.txt` contains the additional testing dependencies.
3. Run the test suite: `pytest test -vs`

If contributing, please add a `test_<module_name>.py` in the `test/` directory
in a subdirectory that matches the wei package directory structure. Inside,
`test_<module_name>.py` implement test functions using pytest.

## Building Documentation

To build the documentation:

1. [Build and install](#developing-wei) wei from source.
2. The `requirements/dev.txt` contains all the dependencies needed to build the documentation.
3. Generate the documentation file via:
```
cd wei/docs
make html
```
The docs are located in `wei/docs/build/html/index.html`.

To view the docs run: `open wei/docs/build/html/index.html`.

## Releasing to PyPI

To release a new version of wei to PyPI:

1. Merge the `develop` branch into the `main` branch with an updated version number in [`wei.__init__`](https://github.com/AD-SDL/wei/blob/main/wei/__init__.py).
2. Make a new release on GitHub with the tag and name equal to the version number.
3. [Build and install](#developing-wei) wei from source.
4. Run the following commands:
```
python3 setup.py sdist
twine upload dist/*
```
