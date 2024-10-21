===============
How-To: Modules
===============

.. admonition:: Note

    This page assumes you've read and understood Core Concepts: :doc:`/pages/concepts/module`. We highly recommend you read it before continuing.

Before Getting Started
======================

There are a few decisions to make before you start writing your own module to integrate a device into WEI:

Helper Class, or Custom Implementation?
---------------------------------------

As part of the ``ad_sdl.wei`` python module, we include a :class:`wei.modules.rest_module.RESTModule` helper class, designed to make it as easy as possible to get started writing a WEI module.

While the helper class has many advantages, it might not always be the right tool for the job. Below are some questions to consider to determine whether the :class:`wei.modules.rest_module.RESTModule` helper class is the right tool for your application:

**Can you interface with your device using Python?**
    In some cases, this is very easy, like if the device manufacturer provides a Python API, or supports control using a common communications standard like serial, HTTP, or I2C. In others, this isn't as straight forward, such as if the vendor provides a .NET dll, but is still very possible (for instance, using `Python.NET <https://pythonnet.github.io/>`_. However, if controlling your device from Python would be difficult or impossible (or if you simply don't want to go that route), then you can forgo the helper class and instead write your own module implementation.

**Do you want to interface with your instrument using REST?**
    The RESTModule helper class is, as the name suggests, an implementation that relies on WEI's REST API-based implementation of the Module Interface standard. While we've generally found REST to be the best solution for our integrations, you may find yourself needing or preferring to implement your module using a different communication standard, such as TCP or ROS2.


Bare-Metal or Containerized?
----------------------------------------

When integrating a new device, we sometimes find it beneficial to "containerize" our module implementation using Docker. Containerization is a powerful tool in any developers toolbelt, but it does come with certain tradeoffs and pitfalls to be mindful of.

Generally, we find that as workcells scale, managing the lifecycls and dependencies of many different modules is much easier when each is sandboxed in its own container, but for many simple cases containerization may be overkill. In addition, because of the hardware-dependent nature of many modules, containerization is not always possible/feasible.

For more on Docker in WEI, consider reading our :doc:`/pages/deployment_guide/docker`.

If you choose *not* to containerize, we recommend you consider alternative strategies for managing your dependencies. With Python-based modules, for instance, consider using `virtual environments <https://docs.python.org/3/library/venv.html>`_, or a tool like pdm, poetry, or conda.

Developing a Module with RESTModule
===================================

For this rest of this guide, we'll assume you're using the :class:`wei.modules.rest_module.RESTModule` python class. If not, you can still follow along, but you'll have to translate to your own language/framework/module interface/etc.

For a quickstart, you can use the `Python Template Module <https://github.com/AD-SDL/python_template_module>`_ as a template for your own implementation.

Creating a New Module
---------------------

First, you need to create a new ``RESTModule`` object:

.. code:: python

    from wei.modules.rest_module import RESTModule

    example_module = RESTModule(
        name="example_module",
        version="0.0.1",
        model="Example-o-tron 5000",
        port=1234, # Default port for the rest server
        description="A useful description of the device/robot/instrument this module can control, and any notable capabilities",
    )

    # Configure your module here!

    if __name__ == "__main__":
        example_module.start()

This instance of the RESTModule class can then be used to define all the functionality of a WEI module for your device integration. ``RESTModule`` is designed to be very customizable and takes a number of additional keyword arguments beyond those enumerated above. But these options should be

The last 2 lines actually run the command line argument parser, initialize the device connection, and start the rest server.

Defining Your Module's Startup and Shutdown
-------------------------------------------

Most modules, regardless of the underlying device, have some startup configuration and some shutdown cleanup to do. This can involve connecting and disconnecting from physical hardware, initializing and cleaning up resources, checking safety and status signals, and so forth.

To support this functionality, we provide the ``startup`` and ``shutdown`` lifecycle decorators, which you can use like so:

.. code:: python

    from starlette.datastructures import State

    @example_module.startup()
    def custom_startup_handler(state: State)
        """Your module's initialization logic goes here"""
        from example_interface import ExampleInterface
        state.example_interface = ExampleInterface(state.device_id)


    @example_module.shutdown()
    def custom_shutdown_handler(state: State)
        """Your module's shutdown logic goes here"""
        state.example_interface.disconnect()

Some things to note:

- The ``state: State`` here is a data structure that, as the name suggests, holds the current state of your module. You'll see it quite a bit in these examples. Think of it as a sort of blackboard you can use to keep track of everything that's going on in your module. We store all the useful members of example_module, as well as any command line parameters, in the ``state`` automatically, and you can easily extend it with additional members as needed (like the ``state.example_interface`` we define above)
- Don't need a startup or shutdown handler? No worries, just leave them out! Some modules are stateless or otherwise don't actually need these kinds of lifecycle functionality and RESTModule is designed to support that.
- The startup handler is called in parallel with the REST server starting up. This often means that the REST server will be up and running before the module is actually ready to do anything. To prevent this from causing too many issues, the RESTModule automatically sets ``status["INIT"] == True`` until the startup handler finishes, and the default action handler (more on that later) will prevent any actions from running until ``status["INIT"] == False``.


Defining Your Module's Action Handlers
--------------------------------------

Now you can start defining the _Actions_ your module can perform. It's up to you to define what those actions are, but generally they will correspond to the commands you can send to your device.

For instance, if your device supports a ``move`` command, you might define an action like this:

.. code:: python
    from starlette.datastructures import State
    from wei.types.step_types import StepResponse, ActionRequest

    @example_module.action(name="move", description="Move the device to a specified position")
    def move_action_handler(state: State, action: ActionRequest, position: float) -> StepResponse:
        """Your action handler logic goes here"""
        state.example_interface.move(position)
        return StepResponse.step_succeeded()

Some things to note:

- The ``name`` keyword argument to the ``action`` decorator defines the name of the action. This is required, and must be unique across all actions defined in your module. If you don't specify a name, the name of the function will be used instead. This name is used in Workflow definitions, so it's a good idea to make it something meaningful.
- The ``description`` keyword argument is optional, and can be used to provide a human-readable description of the action. This can be helpful for documenting your module's actions, and for providing users with context about what the action does. If not provided, the description will be the docstring of the function.
- The ``state: State`` argument provides access to the module's state. This is the same ``state`` object you saw in the startup and shutdown handlers, and you can use it to store whatever you want. It's optional for the action handler, and will only be passed in if you have a ``state`` argument in your function signature.
- The ``action: ActionRequest`` argument is automatically passed in to all action handlers. It contains information about the action being performed, including the action's name, parameters, and files. It is optional for the action handler, and will only be passed in if you have an ``action`` argument in your function signature.
- The ``position: float`` argument is an example of an action parameter. Action parameters are optional, and can be of any JSON serializable type. You can add a description to your parameters to provide additional context about what they represent or how to use them using the ``Annotated[type, description]`` syntax.
- The return value of the function is used to determine the success or failure of the action. If you return a :class:`wei.types.step_types.StepResponse` or :class:`wei.types.step_types.StepFileResponse` object, that will be used directly. If you return nothing (i.e., just ``return``), the action will be assumed to have succeeded. Otherwise, the action will be assumed to have failed, and the module will return ``StepFailed`` with an error message to the client.
