=========
Workcells
=========

TODO: Update

A Workcell is a collection of instruments, robots, and other devices that work in unison to conduct automated Workflows.

Abstractly, a Workcell is a collection of Modules, each of which corresponds to some (typically, though not necessarily) physical device capable of performing an action.

In addition, a Workcell will typically have a number of defined Locations. These Locations correspond to physical points in the space of the Workcell, and often include multiple different representations corresponding to the different coordinate systems used by the various Modules.

Finally, a Workcell has a configuration, which is used to specify various properties and behaviors of the WEI instance that loads the Workcell. These values can also be overridden by the user at runtime using command line parameters.

The Workcell File
=================

A given Workcell is represented declaratively in a YAML file. This file specifies the Modules, Locations, and configuration of the Workcell, and is loaded by WEI when it starts up. This file should comply with the Workcell schema defined in the `wei` package.

As an example, consider the following Workcell file:

.. code-block:: yaml

    name: RPL_Modular_workcell

    #Configuration of the Workcell
    config:
    workcell_origin_coordinates: [9.4307, -10.4176, 0, 1, 0, 0, 0]
    redis_host: "rpl_redis"
    server_host: "rpl_modular_wc_server"

    #List of all components accessible in this workcell
    modules:

    - name: sealer        #Human-legible name specific to an individual component
        active: true        #Mark this module as active or inactive depending on whether or not it's used in the workflow
        model: A4s_sealer   #Type of device being connected to, might be multiple components of same model with different names in a workcell
        interface: wei_rest_node  #Method of communication with the device
        config:   #Relevant communication configuration
            rest_node_address: "http://parker.cels.anl.gov:2000"   #In this case, the rest url used to send actions to the component
        workcell_coordinates: [0,0,0,1,0,0,0]   # X, Y, Z, Q0, Q1, Q2, Q3 relative to workcell_origin_coordinates

    - name: peeler
        model: brooks_peeler
        interface: wei_rest_node
        config:
            rest_node_address: "http://parker.cels.anl.gov:2001"
        workcell_coordinates: [0,0,0,1,0,0,0] # X, Y, Z, Q0, Q1, Q2, Q3

    - name: sciclops
        model: sciclops
        interface: wei_rest_node
        config:
            rest_node_address: "http://parker.cels.anl.gov:2002"
        workcell_coordinates: [0.5713, 1.0934, 1.0514, 0.9831, 0, 0, 0.1826]

    - name: ot2_pcr_alpha
        model: ot2
        interface: wei_rest_node
        config:
            rest_node_address: "http://parker.cels.anl.gov:2003"
        workcell_coordinates: [0,0,0,1,0,0,0]

    - name: ot2_gc_beta
        model: ot2
        interface: wei_rest_node
        config:
            rest_node_address: "http://parker.cels.anl.gov:2004"
        workcell_coordinates: [0,0,0,1,0,0,0]

    - name: ot2_cp_gamma
        model: ot2
        interface: wei_rest_node
        config:
            rest_node_address: "http://parker.cels.anl.gov:2005"
        workcell_coordinates: [0,0,0,1,0,0,0]

    - name: pf400
        model: pf400
        interface: wei_rest_node
        config:
            rest_node_address: "http://strange.cels.anl.gov:3000"
        workcell_coordinates: [0,0,0,1,0,0,0] # X, Y, Z, Q0, Q1, Q2, Q3

    - name: camera_module
        model: camera (logitech)
        interface: wei_rest_node
        config:
            rest_node_address: "http://strange.cels.anl.gov:3001"
        workcell_coordinates: [0,0,0,1,0,0,0]

    - name: hidex
        active: False # Optional flag that marks this module as currently unused
        model: Hidex
        interface: wei_tcp_node
        workcell_coordinates: [0,0,0,1,0,0,0]
        config:
            tcp_node_address: "146.137.240.22"
            tcp_node_port: 2000

    - name: barty
        active: True # Optional flag that marks this module as currently unused
        model: RPL BARTY
        interface: wei_rest_node
        workcell_coordinates: [0,0,0,1,0,0,0]
        config:
            rest_node_address: "http://kirby.cels.anl.gov:8000"
        rest_node_auth: ""

    - name: MiR_base
        active: False # Optional flag that marks this module as currently unused
        model: MiR250
        interface: wei_rest_node
        workcell_coordinates: [0,0,0,1,0,0,0]
        config:
            rest_node_address: "http://mirbase1.cels.anl.gov/api/v2.0.0/"
            rest_node_auth: "/home/rpl/Documents/mirauth.txt"

    - name: ur5
        active: False # Optional flag that marks this module as currently unused
        model: ur5
        interface: wei_ros_node
        workcell_coordinates: [0,0,0,1,0,0,0]
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
    workcell: #Coordinates relative to the workcell origin
        sciclops.exchange: [0.7400, -0.2678, 1.0514, 0.7071, 0, 0, 0.7071]
        sealer.default: [0, 0, 0, 0, 0, 0, 0]
        peeler.default: [0, 0, 0, 0, 0, 0, 0]
        ot2_pcr_alpha.deck1_cooler: [0, 0, 0, 0, 0, 0, 0]
        ot2_growth_beta.deck2: [0, 0, 0, 0, 0, 0, 0]
        ot2_cp_gamma.deck2: [0, 0, 0, 0, 0, 0, 0]
        biometra.default: [0, 0, 0, 0, 0, 0, 0]
        camera_module.plate_station: [0, 0, 0, 0, 0, 0, 0]
        wc.trash: [0, 0, 0, 0, 0, 0, 0]
