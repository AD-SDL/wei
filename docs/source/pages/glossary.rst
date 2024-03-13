========
Glossary
========

TODO: Remove, move into concepts

Action
======

A command that a specific **module** is capable of executing. For example, a robotic arm might support the "transfer" action.
Actions are defined by the **module** itself, and are not defined by WEI. Many actions also accept arguments, used to detail
the specifics of the action to be performed.

Experiment Application
======================

A program that utilizes WEI to control one or more **modules** to conduct an Experiment.
This program can be written in almost any language, though we provide native support for Python via ``wei.experiment_client``.
Since the WEI API is a RESTful web service, any language that can make HTTP requests can be used to control WEI.

Module
======

The combination of a physical instrument, device, robot, or sensor, combined with the software, drivers, and
configuration necessary to control it.

Payload
=======

A dictionary of values that can be swapped into a static **workflow**.
When a **workflow** is submitted with a payload, the payload values are used to replace the corresponding
placeholders in the **workflow**.

WEI will substitute any instances of ``payload.key`` in the workflow file
with the value of ``payload["key"]``.

Protocol (Protocol File)
========================

Certain **modules** require a **protocol file** to be passed to them in order to perform certain device specific actions.
These often take the form of a text file, YAML, XML, JSON, or a unique file formats.

The exact details of the protocol file required for a given module will be documented by the module
of instrument vendor.

Station
=======

A physical location (such as a table, lab bench, or even cart) that can hold one or more **modules**.

Step (Workflow Step)
====================

A single **action** to be performed by a **module**. A **workflow** is composed of one or more of these **steps**.

Run (Workflow Run)
==================

A single execution of a **workflow**. A **workflow** can be submitted multiple times, each time
producing a new **run**. Each **run** is assigned a unique ID.

Workcell
========

A collection of **stations** containing **modules**, as well as defined **locations**. A workcell is defined
by a YAML file, which is loaded by WEI.

Workflow
========

A set of **steps** that are executed in order to complete a task. A workflow is defined by a YAML file, which
an **Experiment Application** can submit to WEI to be run.
