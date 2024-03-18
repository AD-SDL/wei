===========================
Bare-Metal Deployment Guide
===========================

This guide provides instructions for deploying a bare-metal WEI workcell. It assumes that you are deploying an existing WEI-powered workcell. For resources on creating a new workcell, see :ref:`how-to-develop-workcell`.

Installing the WEI Python Package
=================================

Note on platforms: WEI is primarily developed for and tested on Linux. While we have tried to write it to be platform-agnostic, we do not target or test natively on Windows or Mac. If you are using Windows, we recommend using the `Windows Subsystem for Linux (WSL) <https://learn.microsoft.com/en-us/windows/wsl/install>`_.

Installing from PyPi
---------------------

The easiest way to install WEI is to use pip. You can install WEI by running the following command:

``pip install ad_sdl.wei``

This will install the latest version of WEI from the Python Package Index (PyPi). For more details or to see specific versions available, see `the ad_sdl.wei page on PyPi <https://pypi.org/project/ad_sdl.wei/>`_.

Installing from Source
----------------------

Alternatively, you can install WEI from source. To do so, consult the `Install Instructions in the README.md <https://github.com/AD-SDL/wei?tab=readme-ov-file#installation>`_.

Running the WEI Server
======================

The WEI server provides the API for controlling and communicating with the workcell. To start the server, run the following command:

``python -m wei.server --workcell <path/to/workcell.yaml>``

This will start the server and load the workcell configuration from the specified YAML file. The server will listen for incoming connections on port 8000 by default.

Running the WEI Engine
======================

The WEI engine is responsible for the scheduling and execution of workflows and other scheduled operations on the workcell. To start the engine, run the following command:

``python -m wei.engine --workcell <path/to/workcell.yaml>``

This will start the engine and load the workcell configuration from the specified YAML file. The engine will begin scheduling and executing workflows and other operations as they are queued via the WEI Server.

Running Redis
=============

WEI uses Redis to store state and act as a message broker for communication from the server to the engine. You will need to have Redis installed and running in order to use WEI. You can install Redis by following the instructions on the `Redis website <https://redis.io/download>`_.

Configuring the Workcell
========================

There are two methods for configuring the WEI Engine and Server that work in tandem: the workcell YAML file, and command line arguments. The workcell YAML file is the primary method for configuring the workcell, and the command line arguments are used to override the configuration in the workcell YAML file or default values not set in the workcell configuration file.

The only required argument for the WEI Engine and Server is the path to the workcell YAML file.

For a complete breakdown of configuration options, see :class:`wei.core.data_classes.WorkcellConfig`.
