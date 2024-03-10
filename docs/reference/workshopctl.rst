.. _ref_workshopctl:

workshopctl (CLI)
=================

The :program:`workshopctl` tool has subcommands
for reporting SDK health, listing workshops and getting their details;
to invoke a subcommand, add it to your :ref:`SDK hooks <ref_sdk_hooks>`.

:samp:`workshopctl info`
------------------------

This subcommand gets detailed information about a specific workshop:

.. code-block:: console

   $ workshopctl info albert

     name:     albert
     base:     ubuntu@22.04
     project:  /home/user/work/workshop
     status:   pending
     notes:    checking-cuda
     content:
         tensorflow:
             channel:  latest/beta  2024-12-03  56
             message:  Checking if Tensorflow SDK has CUDA enabled


:samp:`workshopctl list`
------------------------

This subcommand lists workshops that use the SDK,
along with their status and additional details if a workshop is not *Ready*:

.. code-block:: console

   $ workshopctl list

     Project          Workshop  Status   Notes
     ~/work/workshop  albert    Error    missing-cuda
     ~/work/workshop  another   Pending  checking-cuda


:samp:`workshopctl set-health`
------------------------------

This subcommand reports the health status of the SDK.
It is essential for the :samp:`check-health` hook
that runs after launch or refresh operations in a workshop:

.. code-block:: shell

   workshopctl set-health [--code=<ERROR CODE>] <STATUS> [<MESSAGE>]


.. list-table::
   :header-rows: 1
   :width: 95
   :widths: 1 2 3

   * - Placeholder
     - Required
     - Value

   * - :samp:`<STATUS>`
     - Required
     - One of :samp:`okay`, :samp:`waiting` or :samp:`error`.

   * - :samp:`<ERROR CODE>`
     - Optional, not allowed with :samp:`okay`
     - Brief code of up to 20 lowercase characters, hyphens and digits;
       should start with a character.

   * - :samp:`<MESSAGE>`
     - Required with :samp:`error-code`
     - User-friendly message explaining the context of the error code;
       7-70 lines long.


Example:

.. code-block:: shell

   workshopctl set-health --code=missing-cuda error "CUDA libraries not found"


See also
--------

Explanation:

- :ref:`exp_workshopctl`


Reference:

- :ref:`ref_sdk_hooks`
