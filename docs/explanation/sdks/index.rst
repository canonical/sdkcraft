.. _exp_sdks:

SDKs
====

.. toctree::
   :hidden:
   :maxdepth: 1

   Hooks <hooks>
   Interfaces <interfaces/index>
   Parts <parts>
   Reporting status <workshopctl>


SDKs are essential workshop components that:

- Install the required system and language packages.

- Configure them
  with hooks, interfaces, parts and other capabilities exposed by `Workshop`_.

- Maintain their own state throughout the lifetime of a workshop.


You define, package and publish an *SDK* at the SDK Store
using |project_markup|'s commands;
it is then consumed by users of :program:`Workshop`,
who download it and use it in their workshops,
possibly combining it with SDKs from other publishers.
SDKs are distributed via :ref:`channels <ref_sdk_channels>` similar to
`snap channels <https://snapcraft.io/docs/channels>`_.


.. _exp_sdk_state:

SDK state
---------

An SDK may store any data specific to it,
such as a model training configuration,
within the workshop.
The publisher of the SDK implements save and restore actions
to let |project_markup| handle such data consistently as the *SDK state*.

Before applying any changes to a workshop
during a :command:`workshop refresh` operation,
|project_markup| saves the SDKs' states
by invoking their :ref:`hooks <exp_sdk_hooks>`.
After a successful change,
the states are respectively restored.


.. _exp_sdk_definition:

SDK definition
--------------

An SDK is defined in a file named :file:`sdkcraft.yaml` that may look like this:

.. code-block:: yaml
   :caption: sdkcraft.yaml

   name: go
   title: Go SDK
   base: ubuntu@20.04
   summary: The Go programming language
   description: |
     Go is an open source programming language that enables the production
     of simple, efficient and reliable software at scale.

   plugs:
     mod-cache:
       interface: content
       target: /home/workshop/go/pkg/mod


|project_markup| consumes this definition when creating an SDK package;
in a real-life scenario, it may include metadata similar to shown above
along with hooks, interfaces (also shown here) and parts
that implement the SDK's functionality.


See also
--------

Explanation:

- :ref:`exp_sdk_hooks`
- :ref:`exp_sdk_interfaces`
- :ref:`exp_sdk_parts`
- :ref:`exp_workshopctl`


Reference:

- :ref:`ref_sdks`