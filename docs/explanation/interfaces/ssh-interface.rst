.. _exp_ssh_interface:

SSH interface
=============

The SSH interface
exposes the host system's SSH agent
to individual SDKs,
allowing them to securely use the host's SSH keys and configuration.

.. _exp_ssh_plug:

SSH interface plug
------------------

An essential element here is the SSH interface plug,
which is declared in the SDK definition.

A basic structure would include just the name of the plug itself
and the interface (:samp:`ssh-agent`).

Defining the plug in an SDK
allows the workshops using this SDK to connect to the host's SSH agent,
which can be useful in various SDK-specific tasks
such as cloning private repositories, accessing remote machines and so on.


.. _exp_ssh_slot:

SSH interface slot
------------------

To let SDKs in a workshop access the host's SSH agent,
:program:`Workshop` provides an SSH interface slot
that multiple SSH interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks that the plug targeting the slot
passes :ref:`validation <exp_interface_connections>`;
if it does,
it can be connected.


Connection
----------

SSH interface plugs aren't connected automatically for security reasons
and require manual connection with the :command:`workshop connect` command.

Establishing a connection means
a proxy Unix domain socket has been created
and a corresponding :envvar:`SSH_AUTH_SOCK` value
has been set for the workshop,
so the host's SSH identities and configuration
are available inside the workshop.


See also
--------

Explanation:

- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_ssh_interface`
