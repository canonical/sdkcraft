.. _exp_gpu_interface:

GPU interface
=============

The GPU interface
enables GPU pass-through
(direct access to the host system's GPUs)
for individual SDKs
to improve the performance of GPU-intensive applications.


.. _exp_gpu_plug:

GPU interface plug
------------------

An essential element here is the GPU interface plug,
which is declared in the SDK definition.

A basic structure would include just the name of the plug itself
and the interface (:samp:`gpu`).

Defining the plug in an SDK
allows the workshops using this SDK to directly access the host's GPU devices,
which may be required for various GPU-intensive workloads.


.. _exp_gpu_slot:

GPU interface slot
------------------

To let SDKs in a workshop access the host's GPUs,
:program:`Workshop` provides a GPU interface slot
that multiple GPU interface plugs can access.

When the SDK is installed at run-time during launch and refresh operations,
:program:`Workshop` checks that the plug targeting the slot
passes :ref:`validation <exp_interfaces_validation>`;
if it does,
it can be connected.


Connection
----------

GPU interface plugs are connected automatically at launch and refresh;
manual connection with the :command:`workshop connect` command is also possible.

Establishing a connection means
the host's GPUs are directly available inside the workshop
via the GPU pass-through mechanism.


See also
--------

Explanation:

- :ref:`exp_sdk_interfaces`


Reference:

- :ref:`ref_gpu_interface`
