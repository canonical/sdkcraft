:hide-toc:

.. _exp_sdk_hooks:

SDK hooks
=========

|project_markup| enables you to define optional life cycle *hooks*
that control and extend the SDK's internal behaviour
to align with `Workshop`_'s logic.

Each hook is a shell script with domain-aware actions
that run in the workshop
at a certain life cycle phase
to ensure the SDK stays functional.
Specific examples include :samp:`setup-base`,
:samp:`save-state` and :samp:`restore-state`.

When you define an SDK,
its hooks should be stored in the :file:`hooks/` subdirectory
beside the :ref:`definition <exp_sdk_definition>`;
|project_markup| verifies and packages them along with the :file:`.yaml` file.


See also
--------

Explanation:

- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_hooks`