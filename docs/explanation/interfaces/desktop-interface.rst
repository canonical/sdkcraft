.. _exp_desktop_interface:

Desktop interface
=================

The Desktop interface
exposes the host system's Wayland socket
to individual SDKs,
allowing them to execute GUI applications
as if they were running on the host directly


.. _exp_desktop_plug:

Desktop interface plug
----------------------

An essential element here is the desktop interface plug,
which is declared in the SDK definition.

A basic structure would include just the name of the plug itself
and the interface (:samp:`desktop`).

Defining the plug in an SDK
allows the workshops using this SDK to connect to the host's Wayland socket,
which can be useful for various SDK-specific tasks such as
building graphical applications or using editors without remote support.


.. _exp_desktop_slot:

Desktop interface slot
----------------------

To let SDKs in a workshop access the host's Wayland socket,
:program:`Workshop` provides a desktop interface slot
that multiple desktop interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks that the plug targeting the slot
passes :ref:`validation <exp_interface_connections>`;
if it does,
it can be connected.


Connection
----------

Desktop interface plugs aren't connected automatically for security reasons
and require manual connection with the :command:`workshop connect` command.

Establishing a connection means a proxy Unix domain socket has been created and the following environment variables have been set:

- :envvar:`WAYLAND_DISPLAY`
  Identifies the name of the Wayland socket
- :envvar:`XDG_SESSION_TYPE`
  Specifies the current display server type
- :envvar:`QT_QPA_PLATFORM`
  Specifies the Qt platform plugin to be used for Qt-based applications
- :envvar:`ELECTRON_OZONE_PLATFORM_HINT`
  Specifies the preferred platform for electron applications


See also
--------

Explanation:

- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_desktop_interface`
