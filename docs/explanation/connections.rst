.. _exp_interface_connections:

How interface connections work
==============================

`Workshop`_ uses a system of interfaces
to manage interactions between SDKs and the host system.


Not APIs, GUIs or CLIs
----------------------

The interfaces are pre-defined,
which enables handling SDKs consistently and uniformly.

Remember that they're not APIs,
nor are they graphical or command-line interfaces,
but rather mechanisms for managing communication.
They implement granular permissions and control
over the usage of resources by a workshop,
determining which hardware or services on the host a workshop can use
and managing that access securely and transparently.


Plugs and slots
---------------

Two important concepts are involved in
:ref:`requesting and granting permissions via an interface <exp_interfaces_plugs_slots>`:

- *Plugs* are attributes of an SDK that needs to access a resource.

- *Slots*, which provide that access, are the attributes of the
  :ref:`agent SDK <exp_agent_sdk>`,
  internal to :program:`Workshop`.


Think of a plug as a cable that needs to be connected to a power socket,
which in turn is the slot.
Each plug is designed to fit into a specific slot,
much like how a power plug only fits into a matching outlet;
thus, a :ref:`content interface <exp_content_interface>` plug
won't connect to an :ref:`SSH interface <exp_ssh_interface>` slot.
When a plug and a slot are eventually connected,
the SDK gains access to the resource or service provided by the slot.


Connections
-----------

What goes into establishing a connection between a plug and a slot?

- **Slot definition**:
  An interface has one or many slots,
  exposed at run-time via the :samp:`agent` SDK.

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
         interface: content
         target: /home/workshop/.ros

       colcon-artefacts:
         interface: content
         target: /home/workshop/colcon

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
  with :command:`workshop connect`, for example:

  .. code-block:: console

     $ workshop connect ros2/ros2:ssh-agent ros2/agent:ssh-agent


  This command fully qualifies both the plug and the slot:

  - First, it specifies the :samp:`ssh-agent` plug
    under the :samp:`ros2` SDK in the :samp:`ros2` workshop.

  - Second, it specifies the :samp:`ssh-agent` interface slot
    under the :samp:`agent` SDK in the same workshop.


  If only the slot name is supplied,
  it's resolved against the workshop's :samp:`agent` SDK,
  so this is equivalent to the previous example:

  .. code-block:: console

     $ workshop connect ros2/ros2:ssh-agent :ssh-agent


Usage
-----

Once the plug is connected,
the SDK can use the resource,
as :command:`workshop connections` shows:

.. code-block:: console

   $ workshop connections

     Interface  Plug                        Slot        Notes
     content    ros2/ros2:colcon-artefacts  :content    manual
     content    ros2/ros2:ros-cache         :content    -
     gpu        ros2/ros2:gpu               :gpu        -
     ssh-agent  ros2/ros2:ssh-agent         :ssh-agent  manual


The user can disconnect the plug manually,
using :command:`workshop disconnect`,
and reconnect it with :command:`workshop connect`;
as the output suggests, manual connections are tracked separately.


See also
--------

Explanation:

- :ref:`exp_sdk_definition`
- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_sdk_definition`
- :ref:`ref_sdk_interfaces`
