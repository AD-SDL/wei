=========
Workcells
=========

A **Workcell** is a collection of :doc:`module` (instruments, robots, and other devices) that work in unison to conduct automated :doc:`workflow`.

Abstractly, a Workcell is defined by three different things: its **Modules**, its **Locations**, and its **Configuration**. All of this is specified in a ``.yaml`` file, which is loaded by the WEI instance that runs the Workcell.

Modules
========

Modules are the individual components that make up a Workcell. These can be anything from a robot arm to a camera to a PCR machine. Each Module has a number of properties, including a name, a model, an interface, and a configuration.

The name of a module in the Workcell is also used in Workflow definitions to specify which module should take an action for a given step.

Locations
==========

A Workcell will often have a number of defined **Locations**. These Locations correspond to physical points in the space of the Workcell, and often include multiple different representations corresponding to the different coordinate systems used by the various Modules.

Configuration
=============

Finally, a Workcell has a configuration, which is used to specify various properties and behaviors of the WEI instance that loads the Workcell. These values can also be overridden by the user at runtime using command line parameters.

To learn how to write your own Workcell file, consult :doc:`/pages/how-to/workcell`.
