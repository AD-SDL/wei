# wei

<!-- TODO: Add badges -->
<!-- [![PyPI version](https://badge.fury.io/py/mdlearn.svg)](https://badge.fury.io/py/mdlearn) -->
<!-- [![Documentation Status](https://readthedocs.org/projects/mdlearn/badge/?version=latest)](https://mdlearn.readthedocs.io/en/latest/?badge=latest) -->

The Workflow Execution Interface (WEI) for Autonomous Discovery/Self Driving Laboratories (AD/SDLs)

For more details and specific examples of how to use wei, please see our [documentation](https://rpl-wei.readthedocs.io/en/latest/).

## Table of Contents
- [wei](#wei)
  - [Table of Contents](#table-of-contents)
  - [Usage](#usage)
  - [Installation](#installation)
  - [Development](#development)
  - [Contributing](#contributing)
  - [Acknowledgments](#acknowledgments)
  - [License](#license)

## Usage

To get started with WEI, we recommend:

- Consulting the [Documentation](https://rpl-wei.readthedocs.io/en/latest/index.html)
- Using the [WEI Template Workcell](https://github.com/AD-SDL/wei_template_workcell) as a starting point to learn how to use WEI, and how to create your own Workcell.

## Installation

To install the `ad_sdl.wei` python package, you can run `pip install ad_sdl.wei`

To install from source, run

```
git clone https://github.com/ad-sdl/wei.git
cd wei
pip install -e .
```

## Development

1. [Install Docker](https://docs.docker.com/engine/install/) for your platform of choice
2. For managing the Python Package, [install PDM](https://pdm-project.org/latest/#installation)
3. For automatic development checks/linting/formatting, [install pre-commit](https://pre-commit.com/)
4. Ensure you have `GNU make` installed (on apt-based systems like Debian and Ubuntu, `sudo apt install make`)
5. Clone the repository.
6. Within the cloned repository, run `make build` to build the python package and docker image locally.

For a complete list of make commands available, run `make help`.


### Using PDM

- [Managing Dependencies](https://pdm-project.org/latest/usage/dependency/)
- [Build and Publish](https://pdm-project.org/latest/usage/publish/)
- [Running Using PDM](https://pdm-project.org/latest/usage/scripts/)

### Using Pre-commit

- To run pre-commit checks before committing, run `pre-commit run --all-files` or `make checks`
- NONE OF THE FOLLOWING SHOULD BE DONE REGULARLY, AND ALL CHECKS SHOULD BE PASSING BEFORE BRANCHES ARE MERGED
    - To skip linting during commits, use `SKIP=ruff git commit ...`
    - To skip formatting during commits, use `SKIP=ruff-format git commit ...`
    - To skip all pre-commit hooks, use `git commit --no-verify ...`
- See [pre-commit documentation](https://pre-commit.com) for more

### Building Documentation

- You can install the documentation python dependencies with `pip install -e '.[docs]'` or `pdm install -G docs`
- You must install [Graphviz](https://graphviz.org/download/)
- You can build the docs with `make docs`

## Contributing

Please report **bugs**, **enhancement requests**, or **questions** through the [Issue Tracker](https://github.com/AD-SDL/wei/issues).

If you are looking to contribute, please see [`CONTRIBUTING.md`](https://github.com/AD-SDL/wei/blob/main/CONTRIBUTING.md).


## Citing

```bibtex
@Article{D3DD00142C,
author ="Vescovi, Rafael and Ginsburg, Tobias and Hippe, Kyle and Ozgulbas, Doga and Stone, Casey and Stroka, Abraham and Butler, Rory and Blaiszik, Ben and Brettin, Tom and Chard, Kyle and Hereld, Mark and Ramanathan, Arvind and Stevens, Rick and Vriza, Aikaterini and Xu, Jie and Zhang, Qingteng and Foster, Ian",
title  ="Towards a modular architecture for science factories",
journal  ="Digital Discovery",
year  ="2023",
pages  ="-",
publisher  ="RSC",
doi  ="10.1039/D3DD00142C",
url  ="http://dx.doi.org/10.1039/D3DD00142C",
abstract  ="Advances in robotic automation{,} high-performance computing (HPC){,} and artificial intelligence (AI) encourage us to conceive of science factories: large{,} general-purpose computation- and AI-enabled self-driving laboratories (SDLs) with the generality and scale needed both to tackle large discovery problems and to support thousands of scientists. Science factories require modular hardware and software that can be replicated for scale and (re)configured to support many applications. To this end{,} we propose a prototype modular science factory architecture in which reconfigurable modules encapsulating scientific instruments are linked with manipulators to form workcells{,} that can themselves be combined to form larger assemblages{,} and linked with distributed computing for simulation{,} AI model training and inference{,} and related tasks. Workflows that perform sets of actions on modules can be specified{,} and various applications{,} comprising workflows plus associated computational and data manipulation steps{,} can be run concurrently. We report on our experiences prototyping this architecture and applying it in experiments involving 15 different robotic apparatus{,} five applications (one in education{,} two in biology{,} two in materials){,} and a variety of workflows{,} across four laboratories. We describe the reuse of modules{,} workcells{,} and workflows in different applications{,} the migration of applications between workcells{,} and the use of digital twins{,} and suggest directions for future work aimed at yet more generality and scalability. Code and data are available at https://ad-sdl.github.io/wei2023 and in the ESI."}
```

## License

WEI is MIT licensed, as seen in the [LICENSE](./LICENSE) file.
