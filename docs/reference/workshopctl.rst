.. _ref_workshopctl:

workshopctl (CLI)
=================

SDKs use the :program:`workshopctl` tool when reporting to the workshop;
to invoke a subcommand, add it to your :ref:`SDK hooks <ref_sdk_hooks>`.


:samp:`workshopctl set-health`
------------------------------

This subcommand reports the health of the SDK.
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
