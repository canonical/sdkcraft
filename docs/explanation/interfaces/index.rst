.. _exp_sdk_interfaces:

SDK interfaces
==============

These articles explain individual interfaces in more detail.

.. toctree::
   :maxdepth: 1

   Content interface <content-interface>
   GPU interface <gpu-interface>
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

Currently, |project_markup| supports the following interfaces:

- :ref:`content interface <exp_content_interface>` (auto-connected)


.. _exp_interfaces_plugs_slots:

Plugs and slots
~~~~~~~~~~~~~~~

To provide access to these resource types,
:program:`Workshop` exposes *interface slots*.
For example, a :ref:`content interface slot <exp_content_interface>`
creates an internal host directory to be mounted inside the workshop;
think of the slot as the provider of the resource.

Further, individual SDKs define *plugs*
to connect to a slot of a certain interface type.

You can think of the plug as the recipient of the resources exposed by the slot;
note that a slot can handle connections with multiple plugs.

This mechanism comes into play when you
:command:`launch` or :command:`start` the workshop;
the plugs defined by its SDKs are automatically connected to the slots,
provided that the definition has all :program:`Workshop` needs to make a match.

When you build an SDK with |project_markup|,
its plugs and slots should be listed in the
:ref:`definition <exp_sdk_definition>`;
each interface will have its own fields and semantics,
including rules to establish connections at run-time.

For details of the connection process, see :ref:`exp_interface_connections`.


See also
--------

Explanation:

- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_interfaces`
