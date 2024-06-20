.. _exp_interface_connections:

How interface connections work
==============================

`Workshop`_ uses a system of interfaces, plugs and slots
to manage permissions and interactions between SDKs and the host system.

Firstly, it's important to remember that :program:`Workshop`'s interfaces
are neither APIs, nor graphical or command-line interfaces,
but rather mechanisms for managing permissions and communication
between SDKs and the host system.
They define specific interaction points and access permissions
that allow granular control over the use of resources in a workshop.

Interfaces determine what resources a workshop can access
(such as specific hardware or host system services)
and ensure that these permissions are managed securely and transparently.

There are a limited number of pre-defined interfaces available,
so they're in fact standardised in :program:`Workshop`
to handle SDK permissions in a consistent, uniform way.


Plugs and slots
---------------

There are :ref:`two important concepts <exp_interfaces_plugs_slots>`
involved in the process of requesting and granting permissions
via the interface mechanism:

- *Plugs* are attributes of an SDK that needs access to a resource or service.

- *Slots*, which provide that access, are the attributes of a
  :ref:`special SDK <exp_agent_sdk>`,
  internal to :program:`Workshop`.


Think of a plug as a cable that needs to be connected to a power socket,
which in turn is the slot.
Each plug is designed to fit into a specific slot,
much like how a power plug only fits into a matching outlet;
thus, a :ref:`content interface <exp_content_interface>` plug
won't connect to a :ref:`SSH interface <exp_ssh_interface>` slot.
When a plug and a slot are eventually connected,
the SDK gains access to the resource or service provided by the slot.


What goes into an connection
----------------------------

- **Plug definition**: When developers create an SDK,
  they list plugs in the :ref:`SDK definition <exp_sdk_definition>`.
  Each plug specifies which interface the SDK needs access to,
  such as a content directory on the host file system or the GPU,
  and additional attributes that may vary by interface:

  .. code-block:: yaml

     plugs:
       ros-cache:
         interface: content
         target: /home/workshop/.ros

       colcon-cache:
         interface: content
         target: /home/workshop/colcon

       gpu:
         interface: gpu


- **Slot declaration**: interface implementations in :program:`Workshop`
  declare slots that are exposed at run-time via the special :samp:`agent` SDK.
  Each slot represents the available resources or services
  that SDKs can connect to,
  and is *eponymous* to an interface.
  In turn, this means that a plug are initially matched to slot
  by the former's :samp:`interface` field value.

  Note that some slot declarations allow multiple plugs per slot,
  as shown for the content interface in the previous example,
  while some, such as the GPU interface, don't need it by design;
  The default behaviour is to set no restrictions.


- **Automatic or manual connection**:
  Some interfaces are auto-connected when the SDK is installed.

  The choice to connect a plug automatically or manually
  depends on the definition of the corresponding slot,
  which may flexibly alter connection rules.
  For instance, a content interface plug can be installed and auto-connected
  based on its slot's declaration alone.
  However, other interfaces may have different rules,
  such as allowing installation but not auto-connection for the SSH interface.

  With interfaces that block auto-connections,
  the user may need to establish the connection manually
  using the :command:`workshop connect` command, for example:

  .. code-block:: console

     $ workshop connect ros2/ros2:colcon-cache ros2/agent:content


  This command fully qualifies both the plug and the slot:
  
  - First, it specifies the :samp:`colcon-cache` plug
    under the :samp:`ros2` SDK in the :samp:`ros2` workshop.

  - Second, it specifies the :samp:`content` interface slot
    under the :samp:`agent` SDK in the same workshop.


  Note that the names of the plug and the slot are different;
  the plug can have an arbitrary name
  but needs to specify :samp:`interface: content` in its definition
  to be successfully connected to this slot.


- **Validation and use**:
  To verify that the SDK can installed and the its plugs can be connected,
  each slot declares its own set of rules;
  rules for automatic or manual connection are but a part of this set.

  Once the plug is connected to the slot,
  the SDK can securely use the resource or service.
  This can be verified with the :command:`workshop connections` command:

  .. code-block:: console

     $ workshop connections

       Interface  Plug                    Slot        Notes
       content    ros2/ros2:colcon-cache  :content    manual
       content    ros2/ros2:ros-cache     :content    -
       gpu        ros2/ros2:gpu           :gpu        -


  The user usually can manually end the connection,
  using :command:`workshop disconnect`,
  and reestablish it with the :command:`workshop connect` command;
  as the example above suggests,
  :program:`Workshop` keeps track of automatic and manual connections.


See also
--------

Explanation:

- :ref:`exp_sdk_interfaces`
- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_definition`