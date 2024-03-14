=======================
Docker Deployment Guide
=======================

This guide will walk you through the process of setting up a WEI deployment using Docker.

Installing Docker
=================

First, you will need to install Docker and Docker Compose. There are multiple ways to install Docker, and the best method will depend on your operating system and your organization's policies. Here are some options:

- `Docker Desktop <https://docs.docker.com/install/>`_: Docker Desktop is a product offered by Docker Inc. that provides a graphical interface for managing Docker containers and images. It will include everything you need to use Docker on your platform, but is a licensed product. At time of writing, it is free for certain users (such as personal and education), but not for large organizations. ANL Users: Docker Desktop is not licensed by ANL and **CAN NOT** be used on ANL computers.
- `Docker Engine <https://docs.docker.com/engine/install/>`_: Docker Engine is the open-source project that Docker Desktop is built on. It is free to use, but does not include a graphical interface. It can only be installed on Linux systems, or in Windows Subsystem for Linux (WSL).
- `Rancher Desktop <https://rancherdesktop.io/>`_: Rancher Desktop is a free, open-source alternative to Docker Desktop. It is built on the same open-source project as Docker Desktop, but is not a licensed product. It is available for Windows, Mac, and Linux. We recommend this option for Mac users.

Other options exist, including `Podman <https://podman.io/>`_. In theory, any container runtime that supports Docker Compose and is compatible with the `Open Container Initiative <https://opencontainers.org/>`_ formats should work, but the reality is that there may be unexpected bugs or incompatibilities and we can't test every option.

Platform Specific Notes
-----------------------

Windows
^^^^^^^

We recommend using `Windows Subsystem for Linux <https://learn.microsoft.com/en-us/windows/wsl/install>`_ (WSL/WSL2) to run Docker. You can install `Docker Desktop`_ (depending on licensing; not on ANL computers) or `Rancher Desktop`_ to provide docker in WSL, or install `Docker Engine`_ directly in WSL.

If you install Docker CE inside WSL without a Docker Desktop/Rancher Desktop install, you will need to manually start the Docker service in WSL after starting WSL. You can do this by running ``sudo systemctl start docker`` in a WSL terminal before invoking docker. Alternatively, you can add ``echo "sudo systemctl --no-pager status docker </dev/null || sudo systemctl start docker"`` to your ``~/.bashrc`` file or equivalent to start the Docker service automatically when you start WSL (note that this will prompt you for a sudo password).

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
    - ``PROJECT_DIR``: The absolute path to the directory containing the workcell, usually the top level directory of the repository.

#. Run ``docker compose up`` in the directory containing the ``compose.yaml`` file (usually the top of the repository, or in ``/docker``). In some cases, there are multiple compose files for a single workcell, such as a compose file for the WEI core services and one or more compose files for modules. In these cases, the individual compose files might have names like ``workcell_name.compose.yml``, and you will need to run ``docker compose -f /path/to/compose.yaml up`` to specify the compose file to use.
#. Upon running this command, you should see a log stream from the containers that are starting up. If you see any errors/container exits, you may need to troubleshoot them (see the Troubleshooting docker section below).
