.. _exp_mount_interface:

SDK mount interface
=====================

The mount interface
exposes host file system locations
to individual SDKs
by mounting them inside the workshop
that references these SDKs.


.. _exp_mount_plug:

Mount interface plug
--------------------

An essential element here is the mount interface plug,
which is declared in the SDK definition.

A basic structure would include the name of the plug itself,
the interface (:samp:`mount`)
and the intended target path inside the workshop (:samp:`workshop-target`).

Defining the plug in an SDK designates the target directory inside the workshop;
a directory on the host system that `Workshop`_ will create at run-time
will be mounted to it.

This allows the workshops using this SDK to use the host directory
(which :program:`Workshop` allocates automatically and doesn't expose otherwise)
to persist the files placed there from inside the workshop
in the host file system when the workshop stops.


.. _exp_mount_slot:

Mount interface slot
--------------------

To let SDKs in a workshop access the host file system,
:program:`Workshop` provides a mount interface slot
that multiple mount interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks the following for each plug that targets the slot:

- The plug can be installed.

- The plug can be auto-connected
  (for :samp:`mount`, it's a yes).

- The :samp:`workshop-target` directory already exists in the workshop.


If the plug passes the checks, it is connected.


Connection
----------

Mount interface plugs are connected automatically at launch and refresh;
manual connection with the :command:`workshop connect` command
or via the workshop definition is also possible.

Establishing a connection means
a directory created by :program:`Workshop` on the host file system
is mounted to the :samp:`target` directory inside the workshop;
the best part is that it's preserved
between :program:`Workshop` operations such as
:command:`workshop refresh`,
:command:`workshop start`
and :command:`workshop stop`,
so you benefit from a pre-populated directory without doing extra work.

Finally, a slot can be remounted to a custom location on the host file system
with the :command:`workshop remount` command.
The new source should be either a non-existing directory
or an empty directory on the same file system as the current source;
otherwise, the workshop must be stopped prior to the remount attempt.


See also
--------

Explanation:

- :ref:`exp_content_sharing`
- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_mount_interface`
