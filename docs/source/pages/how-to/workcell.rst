=================
How-To: Workcells
=================

The Workcell File
=================

A given Workcell is represented declaratively in a YAML file. This file specifies the Modules, Locations, and Configuration of the Workcell, and is loaded by WEI when it starts up. This file should comply with the :class:`wei.core.data_classes.Workcell` schema.

Name
----

.. code-block:: yaml

    name: RPL_Modular_Workcell

The name of the Workcell is specified at the top of the file. This is used by the system to distinguish between different Workcells.

Configuration
-------------

.. code-block:: yaml

    config:
        redis_host: "rpl_redis"
        server_host: "rpl_modular_wc_server"

The configuration section specifies various properties of the Workcell, and determines how the WEI instance that loads the Workcell will behave. All of the values set here can be overridden by the user at runtime using command line parameters for both the WEI Engine and Server.

For a complete breakdown of configuration options, see :class:`wei.core.data_classes.WorkcellConfig`.

Modules
-------

.. code-block:: yaml

    modules:

        - name: sealer        #Human-legible name specific to an individual component
            active: true        #Mark this module as active or inactive depending on whether or not it's used in the workflow
            model: A4s_sealer   #Type of device being connected to, might be multiple components of same model with different names in a workcell
            interface: wei_rest_node  #Method of communication with the device
            config:   #Relevant communication configuration
                rest_node_address: "http://parker.cels.anl.gov:2000"   #In this case, the rest url used to send actions to the component

        - name: peeler
            model: brooks_peeler
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2001"

        - name: sciclops
            model: sciclops
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2002"

        - name: ot2_pcr_alpha
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2003"

        - name: ot2_gc_beta
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2004"

        - name: ot2_cp_gamma
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2005"

        - name: pf400
            model: pf400
            interface: wei_rest_node
            config:
                rest_node_address: "http://strange.cels.anl.gov:3000"

        - name: camera_module
            model: camera (logitech)
            interface: wei_rest_node
            config:
                rest_node_address: "http://strange.cels.anl.gov:3001"

        - name: hidex
            active: False # Optional flag that marks this module as currently unused
            model: Hidex
            interface: wei_tcp_node
            config:
                tcp_node_address: "146.137.240.22"
                tcp_node_port: 2000

        - name: barty
            active: True # Optional flag that marks this module as currently unused
            model: RPL BARTY
            interface: wei_rest_node
            config:
                rest_node_address: "http://kirby.cels.anl.gov:8000"

        - name: MiR_base
            active: False # Optional flag that marks this module as currently unused
            model: MiR250
            interface: wei_rest_node
            config:
                rest_node_address: "http://mirbase1.cels.anl.gov/api/v2.0.0/"
                rest_node_auth: "/home/rpl/Documents/mirauth.txt"

        - name: ur5
            active: False # Optional flag that marks this module as currently unused
            model: ur5
            interface: wei_ros_node
            config:
                ros_node_address: '/ur5_client/UR5_Client_Node'

The ``modules`` section is a list of all the modules that make up the Workcell. Each module is represented by a dictionary with keys for the module's name, model, interface, and configuration. The ``active`` flag is optional and can be used to mark a module as currently unused. The configuration section will vary depending on the specific interface used to communicate with the module.

Locations
---------

.. code-block:: yaml

    locations:
        pf400: #Joint angles for the PF400 Plate Handler
            sciclops.exchange: [223.0, -38.068, 335.876, 325.434, 79.923, 995.062]
            sealer.default: [206.087, -2.27, 265.371, 363.978, 76.078, 411.648]
            peeler.default: [225.521, -24.846, 244.836, 406.623, 80.967, 398.778]
            ot2_pcr_alpha.deck1_cooler: [247.999, -30.702, 275.835, 381.513, 124.830, -585.403]
            ot2_growth_beta.deck2: [163.230, -59.032, 270.965, 415.013, 129.982, -951.510]
            ot2_cp_gamma.deck2: [156, 66.112, 83.90, 656.404, 119.405, -946.818]
            biometra.default: [247.0, 40.698, 38.294, 728.332, 123.077, 301.082]
            camera_module.plate_station: [90.597,26.416, 66.422, 714.811, 81.916, 995.074]
            wc.trash: [259.847, -36.810, 69.090, 687.466, 81.002, 995.035]
        sciclops: #Joint angles for the Sciclops Plate Crane
            sciclops.exchange: [0,0,0,0]

The ``locations`` section is a dictionary of all the locations in the Workcell. Locations are defined relative to each individual module, since different modules will represent the same location in different ways. Each location is represented by a key-value pair of the location's name and the joint angles or other module-specific representation for that location.

Complete Example
----------------

.. code-block:: yaml

    name: RPL_Modular_workcell

    #Configuration of the Workcell
    config:
        redis_host: "rpl_redis"
        server_host: "rpl_modular_wc_server"

    #List of all modules that make up this workcell
    modules:

        - name: sealer        #Human-legible name specific to an individual component
            active: true        #Mark this module as active or inactive depending on whether or not it's used in the workflow
            model: A4s_sealer   #Type of device being connected to, might be multiple components of same model with different names in a workcell
            interface: wei_rest_node  #Method of communication with the device
            config:   #Relevant communication configuration
                rest_node_address: "http://parker.cels.anl.gov:2000"   #In this case, the rest url used to send actions to the component

        - name: peeler
            model: brooks_peeler
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2001"

        - name: sciclops
            model: sciclops
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2002"

        - name: ot2_pcr_alpha
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2003"

        - name: ot2_gc_beta
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2004"

        - name: ot2_cp_gamma
            model: ot2
            interface: wei_rest_node
            config:
                rest_node_address: "http://parker.cels.anl.gov:2005"

        - name: pf400
            model: pf400
            interface: wei_rest_node
            config:
                rest_node_address: "http://strange.cels.anl.gov:3000"

        - name: camera_module
            model: camera (logitech)
            interface: wei_rest_node
            config:
                rest_node_address: "http://strange.cels.anl.gov:3001"

        - name: hidex
            active: False # Optional flag that marks this module as currently unused
            model: Hidex
            interface: wei_tcp_node
            config:
                tcp_node_address: "146.137.240.22"
                tcp_node_port: 2000

        - name: barty
            active: True # Optional flag that marks this module as currently unused
            model: RPL BARTY
            interface: wei_rest_node
            config:
                rest_node_address: "http://kirby.cels.anl.gov:8000"

        - name: MiR_base
            active: False # Optional flag that marks this module as currently unused
            model: MiR250
            interface: wei_rest_node
            config:
                rest_node_address: "http://mirbase1.cels.anl.gov/api/v2.0.0/"
                rest_node_auth: "/home/rpl/Documents/mirauth.txt"

        - name: ur5
            active: False # Optional flag that marks this module as currently unused
            model: ur5
            interface: wei_ros_node
            config:
                ros_node_address: '/ur5_client/UR5_Client_Node'

    locations:
        pf400: #Joint angles for the PF400 Plate Handler
            sciclops.exchange: [223.0, -38.068, 335.876, 325.434, 79.923, 995.062]
            sealer.default: [206.087, -2.27, 265.371, 363.978, 76.078, 411.648]
            peeler.default: [225.521, -24.846, 244.836, 406.623, 80.967, 398.778]
            ot2_pcr_alpha.deck1_cooler: [247.999, -30.702, 275.835, 381.513, 124.830, -585.403]
            ot2_growth_beta.deck2: [163.230, -59.032, 270.965, 415.013, 129.982, -951.510]
            ot2_cp_gamma.deck2: [156, 66.112, 83.90, 656.404, 119.405, -946.818]
            biometra.default: [247.0, 40.698, 38.294, 728.332, 123.077, 301.082]
            camera_module.plate_station: [90.597,26.416, 66.422, 714.811, 81.916, 995.074]
            wc.trash: [259.847, -36.810, 69.090, 687.466, 81.002, 995.035]
        sciclops: #Joint angles for the Sciclops Plate Crane
            sciclops.exchange: [0,0,0,0]
