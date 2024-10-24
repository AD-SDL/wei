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

While the helper class has many advantages, it might not always be the right tool for the job. If you can't or don't want to interface with your device using Python, or if you need to implement a custom module interface, you'll need to write your own module implementation. We'll cover both options below.


Bare-Metal or Containerized?
----------------------------------------

When integrating a new device, we sometimes find it beneficial to "containerize" our module implementation using Docker. Containerization is a powerful tool in any developers toolbelt, but it does come with certain tradeoffs and pitfalls to be mindful of.

Generally, we find that as workcells scale, managing the lifecycles and dependencies of many different modules is much easier when each is sandboxed in its own container, but for many simple cases containerization may be overkill. In addition, because of the hardware-dependent nature of many modules, containerization is not always possible/feasible.

For more on Docker and WEI, consider reading our :doc:`/pages/deployment_guide/docker`.

If you choose *not* to containerize, we recommend you consider alternative strategies for managing your dependencies. With Python-based modules, for instance, consider using `virtual environments <https://docs.python.org/3/library/venv.html>`_, or a tool like pdm, poetry, or conda.

Developing a Module with RESTModule
===================================

For a quickstart, you can use the `Python Template Module <https://github.com/AD-SDL/python_template_module>`_ as a template for your own implementation. You can also use it as a reference to write your own module implementation using the :class:`wei.modules.rest_module.RESTModule` class, or use it to inform your own 100% custom module implementation.

Creating a New Module
---------------------

To define a module using the helper class, first you need to create a new ``RESTModule`` object:

.. code:: python

    from wei.modules.rest_module import RESTModule

    example_module = RESTModule(
        name="example_module",
        version="0.0.1",
        model="Example-o-tron 5000",
        port=1234, # Port for the rest server, defaults to 2000.
        description="A useful description of the device/robot/instrument this module can control, and any notable capabilities",
    )

    # TODO: Configure your module here!

    if __name__ == "__main__":
        example_module.start()

This instance of the RESTModule class can then be used to define all the functionality of a WEI module for your device integration. ``RESTModule`` is designed to be very customizable and takes a number of additional keyword arguments beyond those enumerated above. But these options should be more than enough to get you started.

The last 2 lines in the above example run the command line argument parser, initialize the device connection, and start the rest server.

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
- Don't need a startup or shutdown handler? No worries, just leave them out! Some modules are stateless or otherwise don't actually need these kinds of lifecycle functionality and ``RESTModule`` is designed to support that.
- The startup handler is called in parallel with the REST server starting up. This often means that the REST server will be up and running before the module is actually ready to do anything. To prevent this from causing too many issues, the RESTModule automatically sets ``status["INIT"] == True`` until the startup handler finishes, and the default action handler (more on that later) will prevent any actions from running until ``status["INIT"] == False``.


Defining Your Module's Actions
-------------------------------

Now you can start defining the _Actions_ your module can perform. It's up to you to define what those actions are, but generally they will correspond to the commands you can send to your device.

For instance, if your device supports a ``move`` command, you might define an action like this:

.. code:: python

    from starlette.datastructures import State
    from wei.types.step_types import StepResponse, ActionRequest

    @example_module.action(
        name="move", # *Optional, defaults to the name of the function if not provided.
        description="Move the device to a specified position", # *Optional, will default to the docstring of the function if not provided.
        blocking=True, # *Optional, defaults to True. If True, this action will prevent other actions from running until it finishes. If False, other actions can run concurrently with this one.
    )
    def move_action_handler(
        state: State,
        action: ActionRequest,
        position: Annotated[List[float], "The position to move to, as a list of x, y, and z coordinates"], # *Required argument
        speed: Annotated[float, "The speed at which to move the device, as a percentage of the maximum speed"] = 1.0, # *Optional argument, defaults to 1.0
    ) -> StepResponse:
        """Your action handler logic goes here"""
        state.example_interface.move(position)
        return StepResponse.step_succeeded()

Some things to note about the action function:

- The ``state: State`` argument provides access to the module's state. This is the same ``state`` object you saw in the startup and shutdown handlers, and you can use it to store whatever you want. It's optional for the action handler, and will only be passed in if you have a ``state`` argument in your function signature.
- The ``action: ActionRequest`` argument is available at execution time to all action functions. It contains information about the action being performed, including the action's name, and any arguments or files passed in with the action. It is an optional argument for your action function, and will only be passed in if you have an ``action`` argument in your function signature.
- The ``position`` and ``speed`` arguments are examples of action arguments. Action arguments are optional, and can be of any JSON serializable type. You can add a description to your parameters to provide additional context about what they represent or how to use them using the ``Annotated[type, description]`` syntax.
- The return value of the function is used to determine the success or failure of the action. If you return a :class:`wei.types.step_types.StepResponse` or :class:`wei.types.step_types.StepFileResponse` object, that will be used directly. If you return nothing (i.e., just ``return``), the action will be assumed to have succeeded. Otherwise, the action will be assumed to have failed, and the module will return ``StepFailed`` with an error message to the client.

Action Results
--------------

Let's look at an example of an action that returns results, as both JSON data and file:

.. code:: python

    from starlette.datastructures import State
    from wei.types.step_types import StepFileResponse, ActionRequest
    from wei.types.module_types import ValueModuleActionResult, LocalFileModuleActionResult
    import tempfile


    @example_module.action(
        results=[
            ValueModuleActionResult(
                label="data",
                description="The data returned from the device",
            ),
            LocalFileModuleActionResult(
                label="data_file",
                description="The data returned from the device as a file",
            ),
        ]
    )
    def get_data(
        state: State,
        as_file: Annotated[bool, "Whether to return the data as a file"] = False,
    ) -> StepFileResponse | StepResponse:
        """Get some data from your device and return it."""
        data = state.example_interface.get_data()
        if as_file:
            temp = tempfile.NamedTemporaryFile(delete=False)
            with open(temp.name, "w") as f:
                f.write(data)
            return StepFileResponse(
                status=StepStatus.SUCCEEDED,
                files={
                    "data_file": temp.name,
                },
            )
        return StepResponse(status=StepStatus.SUCCEEDED, data={"data": data})

Note the ``results`` argument in the ``@action`` decorator. This is how you define the results of an action. You can return any number of ``ValueModuleActionResult`` and ``FileModuleActionResult`` objects, and they will be returned to the client as part of the action's response. The argument to the decorator is optional (i.e. even if you don't specify it, the action will still return results), but if you do specify it, users can see the expected results of the action in Module's about information.

You can use StepResponse to return JSON data from an action, or StepFileResponse to return a file and, optionally, JSON data.

To return JSON data, return StepResponse or StepFileResponse with the ``data`` argument set to a dictionary containing the data you want to return. Each top-level key in the dictionary will be used as the label for the result (corresponding to the ``label`` argument passed to a ``ValueModuleActionResult`` in the ``results`` list), and the value will be data to return.

To return one or more files, return StepFileResponse with the ``files`` argument set to a dictionary containing the paths to the files you want to return. Each top-level key in the dictionary will be used as the label for the result (corresponding to the ``label`` argument passed to a ``LocalFileModuleActionResult`` in the ``results`` list), and the value will be the path to the file that will be returned to the client.

Module State
------------

TODO

Module Resources
----------------

.. admonition:: Coming Soon!

    The Resources method is not yet standardized, and is currently under active development.

About Your Module
------------------

The Module's About information is used to provide information about the module, it's actions, and it's resources to the client. It is displayed in the Module's about modal in the dashboard, and returned as part of the module's ``/about`` endpoint.

Module Abouts must conform to the :class:`wei.types.module_types.ModuleAbout` schema.

The RESTModule class automatically generates an about object for your module based on the parameters you set when you create the module instance, arguments to the ``action`` decorators, and properties of the action functions, such as the function signatures. However, you can override this with your own about object if you'd like.

.. code:: python

    from wei.types.module_types import ModuleAbout

    example_module.about = ModuleAbout(
        name="Example Module",
        description="A module for demonstrating how to write your own modules",
    )


Running Your Module and Command Line Arguments
----------------------------------------------

TODO
