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


Example (note only the message is quoted):

.. code-block:: shell

   workshopctl set-health --code=missing-cuda error "CUDA libraries not found"


.. list-table::
   :header-rows: 1
   :width: 95
   :widths: 1 2 3

   * - Placeholder
     - Required
     - Value

   * - :samp:`<STATUS>`
     - Required
     - Can be :samp:`okay`, :samp:`waiting` or :samp:`error`.

   * - :samp:`<ERROR CODE>`
     - Optional, not allowed with :samp:`okay`
     - Short code of lowercase letters, hyphens and digits;
       3–30 characters, should start with a letter.

   * - :samp:`<MESSAGE>`
     - Required with :samp:`error-code`
     - Arbitrary string explaining the context of the error code;
       7–70 characters.


See also
--------

Explanation:

- :ref:`exp_workshopctl`


Reference:

- :ref:`ref_sdk_hooks`
