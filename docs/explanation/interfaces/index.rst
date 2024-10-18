.. _exp_sdk_interfaces:

SDK interfaces
==============

These articles explain individual interfaces in more detail.

.. toctree::
   :maxdepth: 1

   Desktop interface <desktop-interface>
   GPU interface <gpu-interface>
   Mount interface <mount-interface>
   SSH interface <ssh-interface>


Summary
-------

To make SDKs customisable and extensible,
`Workshop`_ implements a counterpart to
:program:`snapd`'s
`interface manager <https://snapcraft.io/docs/interface-management>`__,
which controls whether an SDK can use resources beyond its confines.
You can think of specific interfaces as resource *types*:
file system, hardware, computing and so on.
The interfaces are referenced by the SDKs,
so the user doesn't have direct control over them in the workshop definition.

Remember that they're not APIs,
nor are they graphical or command-line interfaces,
but rather mechanisms for managing resource access.
They implement granular permissions and control
over the usage of resources by a workshop,
determining which hardware or services on the host a workshop can use
and managing that access securely and transparently.

The interfaces are pre-defined,
which enables handling SDKs consistently and uniformly.
Currently,
:program:`Workshop` and |project_markup| support the following interfaces:

- :ref:`mount interface <exp_mount_interface>` (auto-connected)
- :ref:`GPU interface <exp_gpu_interface>` (auto-connected)
- :ref:`desktop interface <exp_desktop_interface>` (manually connected)
- :ref:`SSH interface <exp_ssh_interface>` (manually connected)


.. _exp_interfaces_plugs_slots:

Plugs and slots
---------------

To provide access to these resource types,
:program:`Workshop` exposes *interface slots*.
For example, a :ref:`mount interface <exp_mount_interface>` slot
creates an internal host directory to be mounted inside the workshop;
think of the slot as the provider of the resource.

Further, individual SDKs define *plugs*
to connect to a slot of a certain interface type;
thus, a :ref:`mount interface <exp_mount_interface>` plug
won't connect to an :ref:`SSH interface <exp_ssh_interface>` slot.
You can think of the plug as the recipient of the resources exposed by the slot;
note that a slot can handle connections with multiple plugs.

The first time this mechanism works when you
:command:`workshop launch` or :command:`workshop start` the workshop;
the plugs defined by its SDKs are automatically connected to the slots,
provided that the definition has all :program:`Workshop` needs to make a match.
For manually connected interfaces, this requires :command:`workshop connect`;
either way, the SDK gains access to the resource or service exposed by the slot.

When you build an SDK with |project_markup|,
its plugs and slots should be listed in the
:ref:`definition <exp_sdk_definition>`;
each interface will have its own fields and semantics,
including rules to establish connections at run-time.


.. _exp_interface_connections:

Connection
~~~~~~~~~~

What goes into establishing a connection between a plug and a slot?

- **Slot definition**:
  An interface has one or many slots,
  exposed at run-time via the :ref:`system SDK <exp_system_sdk>`.

  Each slot has a set of rules that determine
  whether an SDK which uses the interface can be installed
  or a plug can be connected to the slot automatically or manually.


- **Plug definition**:
  When you create an SDK,
  list the plugs in the :ref:`SDK definition <exp_sdk_definition>`.
  Each plug specifies an interface your SDK needs
  and additional attributes for that interface:

  .. code-block:: yaml

     plugs:
       ros-cache:
         interface: mount
         workshop-target: /home/workshop/.ros

       colcon-artefacts:
         interface: mount
         workshop-target: /home/workshop/colcon

       gpu:
         interface: gpu


- **Validation and connection**:
  When :program:`Workshop` runs,
  all available slots register themselves with it.

  When a workshop is then launched or refreshed,
  its SDKs and their plugs are validated against the registered slots.
  If no rules prevent it, the SDK is installed,
  then its plugs are matched to the slots by their :samp:`interface` values,
  and all possible auto-connections are established.

  If a slot denies auto-connection,
  the user connects the plug
  with :command:`workshop connect`, for example:

  .. code-block:: console

     $ workshop connect ros2/ros2:ssh-agent ros2/system:ssh-agent


  This command fully qualifies both the plug and the slot:

  - First, it specifies the :samp:`ssh-agent` plug
    under the :samp:`ros2` SDK in the :samp:`ros2` workshop.

  - Second, it specifies the :samp:`ssh-agent` interface slot
    under the system SDK in the same workshop.


  If only the slot name is supplied,
  it's resolved against the workshop's system SDK,
  so this is equivalent to the previous example:

  .. code-block:: console

     $ workshop connect ros2/ros2:ssh-agent :ssh-agent


Usage
~~~~~

Once the plug is connected,
the SDK can use the resource,
as :command:`workshop connections` shows:

.. code-block:: console

   $ workshop connections

     Interface  Plug                        Slot        Notes
     mount      ros2/ros2:colcon-artefacts  :mount      manual
     mount      ros2/ros2:ros-cache         :mount      -
     gpu        ros2/ros2:gpu               :gpu        -
     ssh-agent  ros2/ros2:ssh-agent         :ssh-agent  manual


The user can disconnect the plug manually,
using :command:`workshop disconnect`,
and reconnect it with :command:`workshop connect`;
as the output suggests, manual connections are tracked separately.


See also
--------

Explanation:

- :ref:`exp_sdks`
- :ref:`exp_sdk_definition`


Reference:

- :ref:`ref_sdk_definition`
- :ref:`ref_sdk_plugs_slots`
