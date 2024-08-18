.. _exp_index:

Explanation
===========

These articles iterate over the core set of SDK-related concepts:

.. toctree::
   :maxdepth: 1

   Hooks <hooks>
   Interfaces <interfaces/index>
   Parts <parts>


These topics cover the key principles of SDK usage:

.. toctree::
   :maxdepth: 1

   Data persistence and sharing <data-persistence-sharing>
   Dockerfiles versus SDKs <dockerfile-vs-sdk>
   Health reports <workshopctl>


.. _exp_sdks:

SDKs
----

SDKs are essential workshop components that:

- Install the necessary system and language packages.

- Configure them
  with hooks, interfaces, parts and other capabilities exposed by `Workshop`_.

- Maintain their own state throughout the life cycle of a workshop.


You define, package and publish an SDK in the SDK Store
using |project_markup|'s CLI commands;
the SDK is then consumed by :program:`Workshop` users
who download it and use it in their workshops,
possibly in combination with SDKs from other publishers.
SDKs are distributed through :ref:`channels <ref_sdk_channels>` similar to
`snap channels <https://snapcraft.io/docs/channels>`_.


.. _exp_sdk_state:

SDK state
~~~~~~~~~

An SDK can store any data specific to it,
such as a model training configuration,
within the workshop.
To enable this,
the SDK publisher implements save and restore :ref:`hooks <exp_sdk_hooks>`
that :program:`Workshop` runs at the appropriate moments
to consistently handle such data, collectively known as *SDK state*.

For example, before changes are applied to the workshop
during :command:`workshop refresh`,
the states of the SDKs are saved
by invoking their :samp:`save-state` hooks.
On success,
they are restored using the :samp:`restore-state` hooks.


.. _exp_sdk_definition:

SDK definition
~~~~~~~~~~~~~~

An SDK is defined in a file named :file:`sdkcraft.yaml`,
which may look like this:

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
in a real-world scenario, it may contain metadata similar to that shown above,
along with hooks, more interface plugs and parts
that implement the SDK's functionality.


.. _exp_host_sdk:

Host SDK
~~~~~~~~

Every workshop contains a *host SDK*
that exposes system resources through interface slots.
It's essentially a special SDK type,
which is not available from the SDK Store but is auto-added to each workshop.
It's installed first at :command:`workshop launch`
and removed last at :command:`workshop remove`,
ensuring internal consistency.

The purpose of the host SDK isn't to add hooks or additional content;
it's only there to expose host system resources to other SDKs consistently.
As such, it can't be removed by the user
and isn't listed in the :command:`workshop info` output.

The uniformity of this approach lies in the fact that system resources
and workshop resources are exposed using the same logic.
Technically, the host SDK is of :samp:`host` type,
whereas all other SDKs are of :samp:`regular` type,
but this detail isn't exposed in :file:`sdkcraft.yaml`.


See also
--------

Reference:

- :ref:`ref_sdks`
