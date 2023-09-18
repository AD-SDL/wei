# wei

<!-- TODO: Add badges -->
<!-- [![PyPI version](https://badge.fury.io/py/mdlearn.svg)](https://badge.fury.io/py/mdlearn) -->
<!-- [![Documentation Status](https://readthedocs.org/projects/mdlearn/badge/?version=latest)](https://mdlearn.readthedocs.io/en/latest/?badge=latest) -->

RPL workcell execution interface

For more details and specific examples of how to use wei, please see our [documentation](https://rpl-wei.readthedocs.io/en/latest/).

## Table of Contents
- [wei](#wei)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Install latest version with PyPI](#install-latest-version-with-pypi)
    - [Development install](#development-install)
  - [Testing](#testing)
  - [Usage](#usage)
  - [Contributing](#contributing)
  - [Acknowledgments](#acknowledgments)
  - [License](#license)

## Installation

1. Clone the repository into the desired location. This tutorial will assume it is installed in a folder called `~/workspace/wei`
2. Install [Redis]([200~https://redis.io/docs/getting-started/) and [TMUX](https://github.com/tmux/tmux/wiki/Installing)
3. Within `~/workspace/wei` run the following:

```
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```


## Usage

### Starting the server

1. Update the `folder` variable in `examples/run_wei_server.sh` to point to your WEI install
2. From a new terminal run

```
cd ~/workspace/wei
bash examples/run_wei_server.sh
```

This will run a redis server (window 0), a worker that pulls workflows from a redis-based queue (window 1), and a server that takes incoming workflows from the client and puts them onto the redis-based queue (window 2). It will also run 2 example nodes: a Sleep node and a Camera node.

To test running an experiment, run:

```
python examples/run_example.py
```

## Contributing

Please report **bugs**, **enhancement requests**, or **questions** through the [Issue Tracker](https://github.com/AD-SDL/wei/issues).

If you are looking to contribute, please see [`CONTRIBUTING.md`](https://github.com/AD-SDL/wei/blob/main/CONTRIBUTING.md).


## Acknowledgments

TODO

## License

WEI is MIT licensed, as seen in the [LICENSE](./LICENSE) file.
