===================
Introduction to WEI
===================

WEI is a Python-based tool for automating and managing sequences of instrument and computation actions (**workflows**) in a modular environment in which a variety of hardware and software components implement common interfaces.
This tool leverages ROS (`Robot Operating System <https://www.ros.org>`_) for inter-module communication and `Globus Compute <https://www.globus.org/compute>`_, a 
function-as-a-service platform, for distributed computation. It is particularly geared towards managing 
complex workflows in scientific research and laboratory environments.

WEI allows you to define **workflows** in YAML format. Each workflow comprises a sequence of actions 
(commands), each performed by a specific module. A **module** represents an individual hardware or 
software component in the workcell. This modular approach provides the flexibility to design and 
implement diverse workflows across a variety of domains. 


Overview and Terminology
========================

We define conventional hardware and software configurations for robotic equipment and control software in order to simplify the assembly, modification, and scaling of experimental systems. The following figure shows our hardware conventions:

* A **cart** is a cart with zero or more modules 
* A **module** is a hardware component with a name, type, position, etc. (e.g., Pealer, Sealer, OT2 liquid handling robot, plate handler, plate mover, camera)
* A **workcell**, as shown in the photo on the left of the image below, is formed from multiple (eight in the photo) carts, each typically holding one or more modules (a total of 12 in the example, as described below).
* Multiple workcells and other components can be linked via mobile robots

.. image:: ../assets/AD_Fig.jpg

A **workcell definition** (a YAML file, see below) defines the modules that comprise a workcell, and associated static infrastructure that are to be used by the workflow.

The software associated with a workflow is then defined by three types of files:

* A **driver program**, in Python, sets up to call one or more workflows
* A **workflow definition**, in YAML, define a set of **actions** to be executed, in order, on one or more of the modules in the workcell
* A **protocol definition**, in YAML, defines a set of steps to be performed, in order, on a specified OpenTrons OT2

The figure illustrates the three components for a simple "Color Picker" application that we use to illustrate the use of the technology. 

.. image:: ../assets/ColorPicker.jpg

Workcell definition
-------------------

A workcell definition is a YAML file (e.g., `pcr_workcell.yaml <https://github.com/AD-SDL/rpl_workcell/blob/main/rpl_modular_workcell.yaml>`_) comprising two sections, *config* and *modules*:

The **config** section defines various infrastructure services that may be used elsewhere in the workcell. For example, here is the config from the example just listed.

.. code-block:: yaml

  globus_local_ep: ""                                         # UUID for Globus Transfer endpoint used for local storage
  compute_local_ep: ""                                        # UUID for Globus Compute endpoint used for local computations
  globus_search_index: ""                                     # UUID for the Globus Search instance
  globus_portal_ep: ""                                        # UUID for the portal to which data may be published
  globus_group: "dda56f31-53d1-11ed-bd8b-0db7472df7d6"        # UUID for the group that shares permissions to all UUID's above


The **modules** section lists the *modules* that are included in the workcell. In the example just listed, there are 12 in total: 

* a `pf400 sample handler <https://preciseautomation.com/SampleHandler.html>`_ (**pf400**) and two associated cameras, **pf400_camera_right** and **pf400_camera_left**; 
* a `SciClops plate handler <https://hudsonrobotics.com/microplate-handling-2/platecrane-sciclops-3/>`_ (**sciclops**)
* a `A4S <https://www.azenta.com/products/automated-roll-heat-sealer-formerly-a4s>`_ (**sealer**) and a `Brooks XPeel <https://www.azenta.com/products/automated-plate-seal-remover-formerly-xpeel>`_ (**peeler**), with an associated camera, **sp_module_camera**
* three `OpenTrons OT2 <https://opentrons.com/products/robots/ot-2/>`_ liquid handlers, **ot2_pcr_alpha**, **ot2_pcr_beta**, and **ot2_cp_gamma**;
* a `Biometra thermal cycler <https://www.analytik-jena.com/products/life-science/pcr-qpcr-thermal-cycler/thermal-cycler-pcr/biometra-trio-series/>`_ (**biometra**)
* another camera module, **camera_module**
           
For example, this module specification included in `pcr_workcell.yaml <https://github.com/AD-SDL/rpl_workcell/blob/main/pcr_workcell/pcr_workcell.yaml>`_ described the Sealer module:

.. code-block:: yaml

  - name: sealer                     # A name used for the module in the workflow: its "alias"
    model: sealer                    # Not used at present
    interface: wei_ros_node               # Indicates that module uses ROS2
    config:
      ros_node_address: "/std_ns/SealerNode" # ROS2 network name (in name space)

For other interfaces, a module specification could include things like protocol and IP port.

Workflow definition
-------------------

This is specified by a YAML file that defines the sequence of actions that will be executed in order on the hardware. E.g., see `this example <https://github.com/AD-SDL/rpl_workcell/blob/main/color_picker/workflows/cp_wf_mixcolor.yaml>`_, shown also in the following, and comprising four sections:

* **metadata**: Descriptive metadata for the workflow
* **workcell**: The location of the workcell for which the workflow is designed
* **modules**: A list of the modules included in the workcell--four in this case.
* **flowdef**: A list of steps, each with a name, module, command, and arguments.


.. code-block:: yaml

    name: PCR - Workflow

    metadata:
    - author: Casey Stone, Rafael Vescovi
    - info: Initial PCR workflow for RPL workcell
    - version: 0.1

    modules:
    - name: ot2_cp_gamma
    - name: pf400
    - name: camera

    flowdef:
    - name: Move from Camera Module to OT2
        module: pf400
        action: transfer
        args:
        source: camera_module.positions.plate_station
        target: ot2_cp_gamma.positions.deck2
        source_plate_rotation: narrow
        target_plate_rotation: wide
        comment: Place plate in ot2

    - name: Mix all colors
        module: ot2_cp_gamma
        action: run_protocol
        args:
        config_path:  /home/rpl/workspace/rpl_workcell/color_picker/protocol_files/combined_protocol.yaml
        red_volumes: payload.red_volumes
        green_volumes: payload.green_volumes
        blue_volumes: payload.blue_volumes
        destination_wells: payload.destination_wells
        use_existing_resources: payload.use_existing_resources
        comment: Mix the red portions according to input data

    - name: Move to Picture
        module: pf400
        action: transfer
        args:
        source: ot2_cp_gamma.positions.deck2
        target: camera_module.positions.plate_station
        source_plate_rotation: wide
        target_plate_rotation: narrow

    - name: Take Picture
        module: camera_module
        action: take_picture
        args:
        save_location: local_run_results
        file_name: "final_image.jpg"



This workflow uses three of 12 modules defined in the workcell definition earlier, **pf400**, **ot2_pcr_gamma**, and **camera_module**.
It comprises four steps:

* Transfer a plate from `camera_module.positions.plate_station` to `ot2_cp_gamma.positions.deck2`, while rotating the plate 90 degrees
* Run the "protocol" defined by the file `ot2_pcr_config.yaml <https://github.com/AD-SDL/rpl_workcell/blob/main/color_picker/protocol_files/combined_protocol.yaml>`_. This file specifies a sequence of steps to be performed on the hardware.

* Transfer the plate to the camera
* Take a picture of the plate

> While a workflow and a protocol both specify a sequence of actions to be performed, they are quite different in role and syntax. A **workflow** uses a hardware-independent notation to specify actions to perform on one or more modules (e.g., action A1 on module M1, action A2 on module M2); a **protocol** uses a hardware-specific notation to specify steps to be performed on a single module (e.g., OT2). Why *workflow* and *protocol*? Perhaps because this technology was developed by a partnership of computer scientists ("module", "workflow") and biologists ("protocol")
 
Protocol definition
-------------------

A protocol file gives the device-specific instructions to be executed on a specific piece of hardware to implement an intended action. For example, `ot2_pcr_config.yaml <https://github.com/AD-SDL/rpl_workcell/blob/main/pcr_workcell/protocol_files/ot2_pcr_config.yaml>`_ gives instructions for an OpenTrons OT2. A protocol file specifies a list of **equipment** within the hardware component; a sequence of **commands** to be executed on the equipment; and some describptive **metadata**. For example, the following shows the contents of `combined_protocol.yaml <https://github.com/AD-SDL/rpl_workcell/blob/main/color_picker/protocol_files/combined_protocol.yaml>`_, which comprise the equipment section, three commands, and the metadata section. 

Strings of the form *payload.VARIABLE* (e.g., `payload.destination_wells`) refer to arguments passed to the protocol.

The "location" argument here is OT2-specific: it indicates one of 11 plate locations, numbered 1..11:

.. image:: ../assets/DeckMapEmpty.jpg
    :width: 200px
    
An "alias" argument defines a string that can be used to refer to a position later in the specifrication: e.g., the fourth line in the YAML below specifies that location "7" can be referred to as "source". 

The wells within a plate are referred to via their column and row, e.g., A1. 

The following specification describes an OT2 with the following components:
* In location 7: A 6-well rack of 50 ml tubes. (These are used to contain the different colors that are to be mixed, in wells A1, A2, and A3.
* In each of locations 8 and 9: A 96-well rack of 300 ul wells.

.. code-block:: yaml

    equipment:
    - name: opentrons_6_tuberack_nest_50ml_conical
        location: "7"
        alias: source  # Define "source" as an alias for location 7
    - name: opentrons_96_tiprack_300ul
        location: "8"
    - name: opentrons_96_tiprack_300ul
        location: "9"

    commands:
    - name: Mix Color 1                       # Transfer fluid: A1 -> specified locations 
        source: source:A1
        destination: payload.destination_wells  # Destination wells for transfers (argument)
        volume: payload.red_volumes             # Volumes to be transferred  (argument)
        dispense_clearance: 2
        aspirate_clearance: 1
        drop_tip: False

    - name: Mix color 2
        source: source:A2
        destination: payload.destination_wells
        volume: payload.green_volumes
        dispense_clearance: 2
        aspirate_clearance: 1
        drop_tip: False    
    
    - name: Mix color 3
        source: source:A3
        destination: payload.destination_wells
        volume: payload.blue_volumes
        dispense_clearance: 2
        aspirate_clearance: 1
        mix_cycles: 3
        mix_volume: 100
        drop_tip: False

    metadata:
    protocolName: Color Mixing all
    author: Kyle khippe@anl.gov
    description: Mixing all colors
    apiLevel: "2.12"

Experiment Application
----------------------

A Python program defines the process required to run an experiment. E.g., see `color_picker_application.py <https://github.com/AD-SDL/rpl_workcell/blob/dev_tobias/color_picker/color_picker_application.py>`_ for a color picker program, which calls three workflows: 

* First, if needed, `cp_wf_newplate.yaml`
* Then, the workflow given above, `cp_wf_mixcolor.yaml`
* Finally, as needed, `cp_wf_trashplate.yaml`

The experiment library also gives access to Event functions, which help to create a log of all functions and workflows run during the experiment. The code below shows a simplified version of the color picker, with experiment event annottations, and then the log produced. 

.. code-block:: python

   #!/usr/bin/env python3
   from pathlib import Path
   from rpl_wei.exp_app import Experiment

   def main():
      #Generates the experiment and assigns it an ID
      exp = Experiment('127.0.0.1', '8000', 'Color_Picker')
      #Logs the Experiment with the server
      exp.register_exp() #parser
      payload={}
      #Logs the start of the main loop
      exp.events.loop_start("Main Loop")
      new_plate = True
      exp_budget = 8
      pop_size = 4
      num_exps = 0
      while num_exps + pop_size <= exp_budget:
        #log the decision to get a new plate
        exp.events.decision("Need New Plate", new_plate)
        if (new_plate):
            #Run the WEI workflow to get a new Plate
            test = exp.run_job(Path('new_plate.yaml'),
            payload=payload)
            new_plate=False
        #Log and note the solver run    
        exp.events.log_local_compute("solver.run_iteration")
        solver.run_iteration()
        #Run the WEI Workflow to mix the colors
        test = exp.run_job(Path('mix_colors.yaml'),
        payload=payload)
        #Log and note pulling the colors in  
        exp.events.log_local_compute("get_colors_from_file")
        get_colors_from_file(test.result_file)
        #Publish the Color Picker data to a remote portal
        publish_iter(test)
        
        num_exps += pop_size
        #Mark the end of a loop iteration while checking the loop condition
        exp.events.loop_check("Sufficient Wells In Well Plate", num_exps + pop_size <= exp_budget)
    exp.events.loop_end()
   if __name__ == "__main__":
       main()

This produces a log as below, which will in the future be made compatible with Kafka:

.. image:: ../assets/Log.png
