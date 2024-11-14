.. _exp_camera_interface:

Camera interface
================

The camera interface
exposes the host system's USB cameras and other video capture devices
to individual SDKs.


.. _exp_camera_plug:

Camera interface plug
---------------------

An essential element here is the camera interface plug,
which is declared in the SDK definition.

A basic structure would include just the name of the plug itself
and the interface (:samp:`camera`).

Defining the plug in an SDK
allows the workshops using this SDK to connect to the host's USB-based cameras,
which can be useful in various SDK-specific tasks
such as testing hardware or embedded devices.


.. _exp_camera_slot:

Camera interface slot
---------------------

To let SDKs in a workshop access the host's cameras,
:program:`Workshop` provides a camera interface slot
that multiple camera interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks that the plug targeting the slot
passes :ref:`validation <exp_interface_connections>`;
if it does,
it can be connected.


Connection
----------

Camera interface plugs aren't connected automatically for security reasons
and require manual connection with the :command:`workshop connect` command.

Establishing a connection means
that all currently connected USB-based cameras
will be made available inside the workshop.
New cameras can be added
by disconnecting and then reconnecting the camera interface.


See also
--------

Explanation:

- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_camera_interface`
