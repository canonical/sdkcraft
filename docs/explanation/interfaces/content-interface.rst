.. _exp_content_interface:

SDK content interface
=====================

The content interface
exposes host file system locations
to individual SDKs
by mounting them inside the workshop
that references these SDKs.


.. _exp_content_plug:

Content interface plug
----------------------

An essential element here is the content interface plug,
which is declared in the SDK definition.

A basic structure would include the name of the plug itself,
the interface (:samp:`content`)
and the intended target path inside the workshop.

This definition creates a plug called :samp:`mod-cache`
that does the following:

- Sets its :samp:`interface` type to :samp:`content`,
  making it a content interface plug

- Points the :samp:`target` directory
  to :file:`/home/workshop/go/pkg/mod/`
  *inside the workshop*;
  a directory on the host system
  that `Workshop`_ will designate at run-time
  will be mounted to it


Defining the plug in an SDK
allows the workshops using this SDK to
to use a directory
(which :program:`Workshop` allocates automatically)
to persist the files placed there from inside the workshop
in the host file system
when the workshop stops.


.. _exp_content_slot:

Content interface slot
----------------------

To let SDKs in a workshop access the host file system,
:program:`Workshop` provides a content interface slot
that multiple content interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks the following for each plug that targets the slot:

- The plug can be installed.

- The plug can be auto-connected
  (for :samp:`content`, it's a yes).

- The :samp:`target` directory already exists in the workshop.


If the plug passes the checks, it is connected.


Connection
----------

Content interface plugs are connected automatically at launch and refresh;
manual connection with the :command:`workshop connect` command is also possible.

Establishing a connection means
a directory created by :program:`Workshop` on the host file system
is mounted to the :samp:`target` directory inside the workshop;
the best part is that it's preserved
between :program:`Workshop` operations such as
:command:`workshop refresh`,
:command:`workshop start`
and :command:`workshop stop`,
so you benefit from a pre-populated directory without doing extra work.

Finally, a slot can be remounted to a custom location on the host file system
with the :command:`workshop remount` command.
The new source should be either a non-existing directory
or an empty directory on the same file system as the current source;
otherwise, the workshop must be stopped prior to the remount attempt.


See also
--------

Explanation:

- :ref:`exp_content_sharing`
- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_content_interface`
