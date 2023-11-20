# wei

<!-- TODO: Add badges -->
<!-- [![PyPI version](https://badge.fury.io/py/mdlearn.svg)](https://badge.fury.io/py/mdlearn) -->
<!-- [![Documentation Status](https://readthedocs.org/projects/mdlearn/badge/?version=latest)](https://mdlearn.readthedocs.io/en/latest/?badge=latest) -->

The Workcell Execution Interface (WEI) for Self Driving Laboratories (SDLs)

For more details and specific examples of how to use wei, please see our [documentation](https://rpl-wei.readthedocs.io/en/latest/).

## Table of Contents
- [wei](#wei)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Bare-Metal Install](#bare-metal-install)
    - [Docker Install](#docker-install)
  - [Usage](#usage)
  - [Development](#usage)
  - [Contributing](#contributing)
  - [Acknowledgments](#acknowledgments)
  - [License](#license)

## Installation

### Bare-Metal Install

1. Clone the repository.
2. Install [Redis](https://redis.io/docs/getting-started/) and [TMUX](https://github.com/tmux/tmux/wiki/Installing)
3. Within the cloned repository, run the following:

```
pip3 install --upgrade pip
pip3 install -e '.[examples]'
# Or, without examples:
pip3 install -e .
```

### Docker Install

1. [Install Docker](https://docs.docker.com/engine/install/) for your platform of choice
2. Clone the repository.
3. Within the cloned repository, run the following:

```
docker/build_wei.sh
```

## Usage

### Running the Examples (Bare-Metal Install)

1. Run `examples/run_examples.sh`
2. In the corresponding TMUX session, you should see a number of windows corresponding to each component of WEI. Check each tab to ensure the servers are up and operating properly
3. In the last window, you should see a python command pre-populated. Press enter to run this example experiment script
5. If you have an attached webcam, you can change the `SIMULATED` flag in `examples/experiment_example.py` to False to test taking an actual picture.

### Running the Examples (Docker Install)

1. Run `docker/start_wei.sh`
2. In your browser, navigate to `localhost:8888`
3. Enter `wei` as the token
4. Navigate to `examples/experiment_example.ipynb` and run the cells in the Jupyter Notebook to run an example WEI Experiment
5. If you have an attached webcam, you can change the `SIMULATED` flag to False to test taking an actual picture.

## Development

First, install [pdm](https://pdm-project.org/latest/#installation).

```
pip install pre-commit ruff
pdm install
pre-commit install
```

### Using Pre-commit

- To run pre-commit checks before committing, run `pre-commit run --all-files`
- To skip linting during commits, use `SKIP=ruff git commit ...`
  - This should not be done regularly
- To skip formatting during commits, use `SKIP=ruff-format git commit ...`
  - This should not be done regularly
- To skip all pre-commit hooks, use `git commit --no-verify ...`
- See [pre-commit documentation](https://pre-commit.com) for more

### Using pdm

- [Managing Dependencies](https://pdm-project.org/latest/usage/dependency/)
- [Build and Publish](https://pdm-project.org/latest/usage/publish/)
- [Running Using PDM](https://pdm-project.org/latest/usage/scripts/)
  - `pdm run engine <args>` to start the WEI engine
  - `pdm run server <args>` to start the WEI server
  - `pdm run <arbitrary command>` to run an arbitrary command inside the python environment


## Contributing

Please report **bugs**, **enhancement requests**, or **questions** through the [Issue Tracker](https://github.com/AD-SDL/wei/issues).

If you are looking to contribute, please see [`CONTRIBUTING.md`](https://github.com/AD-SDL/wei/blob/main/CONTRIBUTING.md).


## Acknowledgments

TODO

## License

WEI is MIT licensed, as seen in the [LICENSE](./LICENSE) file.
