.. _exp_workshopctl:

Reporting SDK status with workshopctl
=====================================

The :program:`workshopctl` tool allows an SDK
to talk to the :program:`workshopd` daemon,
giving SDK authors a way to manage health checks and report status.
Using a model similar to `snapctl <https://snapcraft.io/docs/using-snapctl>`_,
it simplifies internal workshop communication,
helping both SDK authors and users.


Introduction
------------

:program:`workshopctl` is a CLI tool
that an SDK author can use in the :ref:`SDK hooks <exp_sdk_hooks>`
to communicate with the :program:`workshopd` daemon.
Under the hood, :program:`workshopctl` uses a socket exposed by the daemon
to fit seamlessly into the workshop environment.

This interaction between SDKs and the :program:`workshopd` daemon
focuses on health checks in post-launch or refresh operations.
The tool offers commands to report SDK health,
list workshops that use the SDK and get their details.


Setting SDK health
------------------

A primary function of :program:`workshopctl` is
to allow SDKs to report their health
using the :samp:`set-health` subcommand.
This command allows to report important information about the state of an SDK
after the workshop that uses the SDK is launched or refreshed.

To use the command with :program:`workshopctl`,
you specify the mandatory health status.
If it's not :samp:`okay`,
you can also supply an error code with a user-friendly message
to provide further details.

This command is essential for SDK authors
to communicate the health status of their individual SDKs
within the workshop environment;
the daemon does the rest to determine the overall health status of a workshop.


Determining workshop health
---------------------------

The :samp:`check-health` hook is central in this
because it communicates the SDK health status to the :program:`workshopd` daemon
during workshop launch or refresh operations.
The status of a workshop, such as *Ready*, *Pending* or *Error*,
depends on the hook's run-time results:

- *Ready* means success, achieved if the hook sets the status to :samp:`okay`
  or exits gracefully with a zero code.

- *Pending*: used when the hook sets the status to :samp:`waiting`,
  which changes to :samp:`error` after 10 unsuccessful retries, one per second,
  or 5 initial seconds elapsing without :samp:`set-health` being invoked.

- *Error* occurs when the hook exits with an error code
  or explicitly sets :samp:`error` as the health status.


See also
--------

Explanation:

- :ref:`exp_sdk_hooks`


Reference:

- :ref:`ref_workshopctl`
