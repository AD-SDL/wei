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
 2. within `~/workspace/wei` run the following code block: 

```
conda create -n rpl-wei python=3.9
conda activate rpl-wei
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```


## Usage

### Starting the server

from a new terminal run
```
cd ~/workspace/wei 
sudo apt install tmux
bash scripts/run_wei_server.sh
```

This will run 3 programs, a redis queue system (window 0), a worker that pulls workflows from the redis queue (window 1), and a server that takes incoming workflows from the client and puts them onto the redis queue(window 2).  

## Contributing

Please report **bugs**, **enhancement requests**, or **questions** through the [Issue Tracker](https://github.com/AD-SDL/wei/issues).

If you are looking to contribute, please see [`CONTRIBUTING.md`](https://github.com/AD-SDL/wei/blob/main/CONTRIBUTING.md).


## Acknowledgments

TODO

## License

<!-- wei has a TODO license, as seen in the [LICENSE](https://github.com/ramanathanlab/mdlearn/blob/main/LICENSE) file. -->
