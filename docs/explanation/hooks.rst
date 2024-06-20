:hide-toc:

.. _exp_sdk_hooks:

SDK hooks
=========

|project_markup| allows you to define optional life cycle *hooks*
that control and extend the of the SDK to match the logic of `Workshop`_.

Each hook is a shell script with domain-aware actions
that are executed in the workshop
at a particular life cycle stage
to ensure that the SDK stays functional.
Specific examples include :samp:`setup-base`,
:samp:`save-state` and :samp:`restore-state`.

When you define an SDK,
its hooks should be placed in the :file:`hooks/` subdirectory
next to the :ref:`definition <exp_sdk_definition>`;
|project_markup| validates and packages them along with the :file:`.yaml` file.


See also
--------

Explanation:

- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_hooks`