.. _exp_sdk_interfaces:

SDK interfaces
==============

.. toctree::
   :glob:
   :hidden:

   Content interface <content-interface>
   Data sharing <content-sharing>


To make SDKs customisable and extensible,
`Workshop`_ implements a counterpart to
:program:`snapd`'s
`interface manager <https://snapcraft.io/docs/interface-management>`__,
controlling whether an individual SDK can use resources beyond its confinement.
You can think of specific interfaces as resource *types*:
file system, hardware, computational and so on.


.. _exp_interfaces_plugs_slots:

Plugs and slots
---------------

In order to provide access to these resource types,
:program:`Workshop` exposes so-called *interface slots*.
For instance, a :ref:`content interface slot <exp_content_interface>`
creates a designated host directory to be mounted inside the workshop;
think of the slot as the provider of the resource.

On top of that, individual SDKs define *plugs*
to connect to a slot that belongs to a certain interface.

You can think of the plug as the recipient of the resources exposed by the slot;
note that a slot can handle connections with multiple plugs.

Eventually, this mechanism starts whirring when the workshop itself is started;
the plugs defined by its SDKs are automatically connected to the slots,
provided the definition contains everything
:program:`Workshop` needs to make a match.

When you build an SDK with |project_markup|,
its plugs and slots should be listed in the
:ref:`definition <exp_sdk_definition>`;
each interface will have its own fields and semantics.


.. _exp_interfaces_validation:

Validation and policies
-----------------------

Also, to make sure plugs can be installed and auto-connected,
each interface uses its own set of rules called policies.
For example, the content interface plug can be installed and auto-connected
based on its policy alone.
However, other interfaces may have different rules,
such as enabling installation but not auto-connection for :samp:`ssh-agent`.


See also
--------

Explanation:

- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_interfaces`