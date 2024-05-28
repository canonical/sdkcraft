.. _ref_sdks:

SDKs
====


.. _ref_sdk_directory:

Source directory
----------------

All files that go into an SDK should be placed in a *source directory*
where you'll run |project_markup|
to initialise, define, pack and publish the SDK.


.. _ref_sdk_definition:

SDK definition
--------------

The name of the workshop definition file must be :file:`sdkcraft.yaml`;
the file is usually created using the :command:`sdkcraft init` command
in the source directory.

The definition in the file must be written in
`YAML <https://yaml.org/>`__
and include these top-level fields:
:samp:`name`, :samp:`base`, :samp:`version`, :samp:`summary`,
:samp:`description`, :samp:`license`, :samp:`platforms` and :samp:`parts`.
The :samp:`plugs` field is optional.

.. list-table::
   :header-rows: 1
   :width: 95
   :widths: 1 1 7

   * - Key
     - Value
     - Description

   * - :samp:`name`
     - string
     - SDK's name, used to reference it in the workshop definition.


   * - :samp:`base`
     - string
     - SDK's base image
       that provides the underlying OS capabilities.

       It can be :samp:`ubuntu@20.04` or :samp:`ubuntu@22.04`.


   * - :samp:`version`
     - string
     - SDK's arbitrary version;
       semantic versioning is recommended.

       .. note::

          Use quotes to avoid potential data type mismatches:
          without them, :samp:`'1.0'` can be interpreted as a number,
          for example.


   * - :samp:`summary`
     - string
     - A short one-line summary of up to 79 characters.


   * - :samp:`description`
     - string
     - A longer, more detailed description of the SDK, up to one hundred words.


   * - :samp:`license`
     - string
     - Name of the software license under which the SDK is distributed.

       .. note::

          Make sure it matches the individual components of the SDK.


   * - :samp:`platforms`
     - object
     - Lists individual architectures that the SDK supports.


   * - :samp:`parts`
     - object
     - See :ref:`ref_sdk_parts` for a detailed discussion.


   * - :samp:`plugs`
     - object
     - See :ref:`ref_sdk_interfaces` for a detailed discussion.


For example:

.. code-block:: yaml
   :caption: sdkcraft.yaml

    name: go
    title: Go SDK
    base: ubuntu@22.04
    summary: The Go programming language
    description: |
      Go is an open source programming language that enables the production
      of simple, efficient and reliable software at scale.
    version: '0.1'
    license: LGPL-2.1
    platforms:
        amd64:

    parts:
      go-part:
        plugin: nil

    plugs:
      mod-cache:
        interface: content
        target: /home/workshop/go/pkg/mod


JSON Schema
~~~~~~~~~~~

The following
`JSON Schema <https://json-schema.org/>`__
formalises the description above:

.. literalinclude:: schema.json
   :language: json


.. _ref_sdk_parts:

SDK parts
---------

Parts can be though of as the building blocks of |project_markup|.
Each part in an :file:`sdkcraft.yaml` :ref:`file <ref_sdk_definition>`
defines a specific component or piece of the SDK being packaged,
providing a way to modularise the package and manage its dependencies.

|project_markup| is built as a
`craft-application <https://github.com/canonical/craft-application>`_,
which affects how :samp:`parts` are implemented.
However, note that :samp:`stage-packages` and :samp:`stage-snaps`
aren't enabled yet;
instead, rely on the :ref:`hooks <ref_sdk_hooks>`
to implement custom logic of package and snap installation.


.. _ref_sdk_interfaces:

SDK interfaces
--------------

Currently, the only interface supported by |project_markup| is :samp:`content`.
It maps a directory in the workshop to a predefined directory on the host;
`Workshop`_ is responsible for mapping the internal directory
to a default directory on the host,
and the SDK is responsible for handling the contents of the directory.

An example that lists the name of the plug, the interface
and the intended target path in the workshop:

.. code-block:: yaml
   :caption: sdkcraft.yaml

    # ...
    plugs:
      mod-cache:
        interface: content
        target: /home/workshop/go/pkg/mod


This maps the :file:`/home/workshop/go/pkg/mod/` directory inside the workshop
to a directory created by :program:`Workshop` on the host.


.. _ref_sdk_hooks:

SDK hooks
---------

|project_markup| supports the following life cycle hooks:

.. list-table::
   :header-rows: 1
   :width: 95
   :widths: 2 5 4

   * - Name
     - When it runs
     - What it does

   * - :samp:`check-health`
     - At :command:`workshop launch`:
       after running :samp:`setup-base` hooks for *all* SDKs.
     
       At :command:`workshop refresh`:
       after running :samp:`restore-state` hooks for *all* SDKs.

     - Reports the state of the SDK
       (*OK*, *waiting* or *error*)
       for :program:`Workshop`
       to determine the overall status of the workshop,
       using the :program:`workshopctl` internal CLI tool.


   * - :samp:`restore-state`

     - At :command:`workshop refresh`:
       after launching the new workshop
       and running the :samp:`setup-base` hook for the SDK.

     - Restores SDK-specific data from the :ref:`state directory <ref_sdk_state>`.
       The hook itself comes from the *new* SDK version.


   * - :samp:`save-state`

     - At :command:`workshop refresh`:
       before destroying the old workshop.

     - Saves SDK-specific data to the :ref:`state directory <ref_sdk_state>`.
       The hook itself comes from the *old* SDK version.


   * - :samp:`setup-base`

     - At :command:`workshop launch`, :command:`workshop refresh`:
       after unpacking the base image
       and starting the workshop,
       but before setting its status to *Ready*.

     - Configures the base image for the SDK to become operational.


Each hooks is defined in a text file of the same name
under :samp:`hooks/` in the :ref:`source directory <ref_sdk_directory>`.
At run-time, they are executed as shell scripts
under :samp:`root` inside the workshop,
so each hook must start with a shebang directive,
for example:

.. code-block:: shell

   #!/usr/bin/bash


.. note::

   The hooks aren't mentioned in the :ref:`definition <ref_sdk_definition>`;
   |project_markup| automatically enumerates them when packing the SDK.


.. _ref_sdk_state:

SDK state
---------

An SDK cat store any data specific to it within the workshop.
For this purpose, an environment variable named :envvar:`$SDK_STATE_DIR`
is exposed by :program:`Workshop` at run-time;
it resolves to an internal directory in the workshop,
which :samp:`save-state` and :samp:`restore-state`
can use to preserve and recover the data respectively.


.. _ref_sdk_channels:

SDK channels
------------

When SDKs are published by their creators and consumed by workshops,
different versions and releases are tracked through the use of channels.
A channel is a combination of a track and a risk, e.g. :samp:`latest/beta`.

Tracks allow multiple published versions of an SDK to exist in parallel;
while no specific scheme is enforced,
it is desirable to use a semantic version, e.g. :samp:`1.2.3`,
or the :samp:`latest` keyword,
which maps to the latest published version and serves as the default.

Risks represent a choice of maturity levels for a particular track:

- :samp:`stable`: indicates that the software can be used in production

- :samp:`candidate`: for software that's being tested prior to stable deployment

- :samp:`beta`: for software that can be used outside of production

- :samp:`edge`: for unstable software that's still in active development;
  nothing is guaranteed


See also
--------

Explanation:

- :ref:`exp_sdks`