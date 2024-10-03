=======================
Docker Deployment Guide
=======================

This guide will walk you through the process of setting up a WEI deployment using Docker.

Installing Docker
=================

First, you will need to install Docker and Docker Compose. There are multiple ways to install Docker, and the best method will depend on your operating system and your organization's policies. Here are some options:

- `Docker Desktop <https://docs.docker.com/install/>`_: Docker Desktop is a product offered by Docker Inc. that provides a graphical interface for managing Docker containers and images. It will include everything you need to use Docker on your platform, but is a licensed product. At time of writing, it is free for certain users (such as personal and education), but not for large organizations. ANL Users: Docker Desktop is not licensed by ANL and **CAN NOT** be used on ANL computers.
- `Rancher Desktop <https://rancherdesktop.io/>`_: Rancher Desktop is a free, open-source alternative to Docker Desktop. It is built on the same open-source project as Docker Desktop, but is not a licensed product. It is available for Windows, Mac, and Linux. We recommend this option for Mac and Windows users.
- `Docker Engine <https://docs.docker.com/engine/install/>`_: Docker Engine is the open-source project that Docker Desktop is built on. It is free to use, but does not include a graphical interface. It can only be installed on Linux systems, or in Windows Subsystem for Linux (WSL).

Other options exist, including `Podman <https://podman.io/>`_. In theory, any container runtime that supports Docker Compose and is compatible with the `Open Container Initiative <https://opencontainers.org/>`_ formats should work, but the reality is that there may be unexpected bugs or incompatibilities and we can't test every option.

Platform Specific Notes
-----------------------

Windows
^^^^^^^

We recommend using `Windows Subsystem for Linux <https://learn.microsoft.com/en-us/windows/wsl/install>`_ (WSL/WSL2) to run Docker. You can install `Docker Desktop`_ (depending on licensing; not on ANL computers) or `Rancher Desktop`_ to provide docker in WSL.

After installing WSL and either Rancher Desktop or Docker Desktop, you will need to go into the Desktop application's preferences and enable the WSL integration. This will allow you to use the Docker CLI in WSL.

If using Rancher Desktop, make sure you select the ``dockerd (moby)`` container engine during install or in the preferences.

Mac
^^^

We recommend using `Rancher Desktop`_ to run Docker. This is the current solution for developers using Mac on our own team, and therefore the best tested solution. Alternatively, `Docker Desktop`_ is also an option (depending on licensing; not on ANL computers).

For `Rancher Desktop`_, some settings are currently required to avoid permissions issues with bind-mounted volumes:

- Under ``Preferences -> Container Engine -> General``, select ``dockerd (moby)``
- Under ``Preferences -> Virtual Machine -> Emulation``, select ``VZ``
- Under ``Preferences -> Virtual Machine -> Volumes``, select ``virtiofs``

Linux
^^^^^

We recommend using `Docker Engine`_ to run Docker. This is the current solution for developers using Linux on our own team, and therefore the best tested solution. Alternatively, `Docker Desktop`_ is also an option (depending on licensing; not on ANL computers), and `Rancher Desktop`_ should also work.

Using Docker and Docker Compose
===============================

Docker and Docker Compose are complex, powerful tools with many features, and it would be impossible to cover them in great detail here. This guide will only cover the basics needed to run WEI. For more information, see the `Docker documentation <https://docs.docker.com/>`_ and `Docker Compose documentation <https://docs.docker.com/compose/>`_, as well as any relevant documentation for the specific implementation you are using (e.g. `Rancher Desktop documentation <https://rancherdesktop.io/docs/>`_).

There are also many great articles, blogs, tutorials, and cheatsheets covering these tools for beginners. A few examples:

- `Docker Quickstart <https://docs.docker.com/get-started/>`_
- `Docker Cheatsheet <https://dockerlabs.collabnix.com/docker/cheatsheet/>`_
- `Docker Compose Quickstart <https://docs.docker.com/compose/gettingstarted/>`_

While we've done our best to handle or abstract away as much of the complexity as possible in our implementations, you will still need to understand some of the basics of Docker and Docker Compose to troubleshoot issues or customize your deployment. At the very least, we recommend you familiarize yourself with the following concepts:

- Containers
- Images
- Dockerfiles
- Compose Files
- Environment Files
- Volumes

We will assume you have a basic understanding of these concepts in the rest of this guide.

Deploying a Dockerized Workcell
===============================

Starting a workcell that has already been dockerized is as simple as the following:

#. Copy the ``example.env`` file, if it exists, to ``.env``. This file contains environment variables that are used to configure the workcell and docker compose stack. You will need to edit this file to match your specific deployment. For example, you will most likely need to set/change the following:

    - ``USER_ID``: The user ID of the user running in the container. This is used to ensure that files created by the container are owned by the correct user on the host system. You can find your user ID by running ``id -u`` in a terminal on Linux/WSL/Mac.
    - ``GROUP_ID``: The group ID of the user running in the container. This is used to ensure that files created by the container are owned by the correct group on the host system. You can find your group ID by running ``id -g`` in a terminal on Linux/WSL/Mac.

#. Run ``docker compose up`` in the directory containing the ``compose.yaml`` file (usually the top of the repository, or in ``/docker``). In some cases, there are multiple compose files for a single workcell, such as a compose file for the WEI core services and one or more compose files for modules. In these cases, the individual compose files might have names like ``workcell_name.compose.yml`` or ``hostname.compose.yml``, and you will need to run ``docker compose -f /path/to/file.yaml up`` to specify the compose file to use.
#. Upon running this command, you should see a log stream from the containers that are starting up. If you see any errors/container exits, you may need to troubleshoot them.
#. You can now access the workcell using the WEI Experiment Client or using the REST API via the hostname/ip address of the machine you started the main docker compose stack on, and the port specified for the WEI Server in the workcell configuration file and/or docker compose file (default is 8000).

Deploying a Dockerized Workcell with Non-dockerized Modules
-----------------------------------------------------------

It is often the case that a dockerized workcell will need to interact with non-dockerized modules. This occurs most often for devices that depend on Windows Drivers, Graphical User Interfaces, or other software that is difficult to run in a container. In these cases, the non-dockerized modules will need to be started manually. Often a script and/or documentation will be included in the repository to help you do this.

Fortunately, as long as the device's module is reachable over the network, these modules should integrate seamlessly with an otherwise dockerized workcell.

Dockerizing a Workcell
======================

If you have an existing workcell that you would like to dockerize, or want to create a new workcell from scratch and dockerize it, we recommend the `WEI Template Workcell <https://github.com/AD-SDL/wei_template_workcell>`_. This repository contains a complete example of a workcell that has been dockerized, and can be used as a starting point for your own workcell.

The basic requirements to dockerize a workcell are as follows:

- Create a ``compose.yaml`` file that includes, at a minimum, the WEI core services (the WEI Server, WEI Engine, and a Redis Instance). An example of the core services files can be found in the `WEI Template Workcell`_
- Create docker compose services for any dockerized modules in your workcell. These can be in your main ``compose.yaml`` file, in separate files that are imported into the main file via the `Include top-level element <https://docs.docker.com/compose/multiple-compose-files/include/>`_, or in independent files (for instance, if you need to run certain modules on a different host machine).
- Update your workcell's configuration file and/or command line arguments to use the correct hostnames for dockerized modules and workcell components. When a docker container wants to communicate with another docker container in the same Docker Network (generally, another container started by the same docker compose command), it can do so via the Docker Network's DNS names, which default to the `container_name` from the docker compose service. Some common examples:
    - If you set your WEI Server container name via ``container_name: wei_server`` and have it exposed on port 8000, you can access it from other containers in the same compose network as ``http://wei_server:8000``, rather than as ``http://localhost:8000``. So in order for the WEI Engine to communicate with the WEI Server, you need to either include ``--server_host=wei_server --server_port=8000`` in the WEI Engine's ``command``, or set the ``server_host`` and ``server_port`` keys in the workcell configuration file's config section.
    - Similarly, if you set your Redis service to be named ``wei_redis``, you must either include ``--redis_host=wei_redis`` in the WEI Server and WEI Engine's ``command``, or set ``redis_host`` in the workcell file's config.
    - Finally, if you have a module that is dockerized and `on the same Docker network as the WEI Engine and Server`, you will need to update the hostname and/or port for that module in the workcell's config for that module. If, however, the module is on a separate machine from the WEI Engine, continue to use the hostname/IP address of the host machine.
