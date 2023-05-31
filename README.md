# rpl_wei

<!-- TODO: Add badges -->
<!-- [![PyPI version](https://badge.fury.io/py/mdlearn.svg)](https://badge.fury.io/py/mdlearn) -->
<!-- [![Documentation Status](https://readthedocs.org/projects/mdlearn/badge/?version=latest)](https://mdlearn.readthedocs.io/en/latest/?badge=latest) -->

RPL workcell execution interface

For more details and specific examples of how to use rpl_wei, please see our [documentation](https://rpl-wei.readthedocs.io/en/latest/).

## Table of Contents
- [rpl_wei](#rpl_wei)
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

### Development install 
```
conda create -n rpl-wei python=3.9
conda activate rpl-wei
pip3 install --upgrade pip setuptools wheel
pip3 install -r requirements/dev.txt
pip3 install -r requirements/requirements.txt
pip3 install -e .
```

## Testing

TODO under new design

## Usage

### Starting the server
*\*Requires three terminals\**
1. Start redis. I have a `redis.conf` file in the root of the repo. You can use it with `envsubst` to replace the environment variables with their values as redis does not support environment variables in the config file.
```
envsubst < redis.conf | redis-server -
```
1. Start rq worker
```
python -m rpl_wei.processing.worker
```
1. Start the server
```
python -m rpl_wei.server --workcell tests/test_pcr_workcell.yaml
```
TODO: look at something like `systemd`, `supervisord`, or `Docker` to manage the processes


## Contributing

Please report **bugs**, **enhancement requests**, or **questions** through the [Issue Tracker](https://github.com/AD-SDL/rpl_wei/issues).

If you are looking to contribute, please see [`CONTRIBUTING.md`](https://github.com/AD-SDL/rpl_wei/blob/main/CONTRIBUTING.md).


## Acknowledgments

TODO

## License

<!-- rpl_wei has a TODO license, as seen in the [LICENSE](https://github.com/ramanathanlab/mdlearn/blob/main/LICENSE) file. -->
