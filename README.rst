SDKcraft
========

.. image:: https://github.com/canonical/sdkcraft/actions/workflows/qa.yaml/badge.svg
   :target: https://github.com/canonical/sdkcraft/actions/workflows/qa.yaml
   :alt: QA Status

**Build and publish the SDKs that power Workshop's Ubuntu-native development environments.**

SDKcraft is Canonical's tool for packaging languages, libraries, tools, and services
as reusable SDKs for `Workshop <https://github.com/canonical/workshop>`_.
Define what an SDK contains, how it is set up, and which interfaces it uses.
Workshop then composes SDKs into development environments for individual projects.

Use SDKcraft to share a toolchain with your team
or publish components that other Workshop users can add to their projects.

- **Declarative**: describe an SDK's metadata, target platforms, parts, and interfaces
  in ``sdkcraft.yaml``, with hooks for runtime setup and lifecycle operations.
- **Composable**: package functionality that connects to other SDKs
  and host resources through Workshop interfaces.
- **Testable**: try an SDK locally and run its tests before publishing.
- **Distributable**: publish SDK revisions to the SDK Store
  and release them through channels.


Installation
------------

SDKcraft is available on Ubuntu and other ``snap``-enabled Linux distributions.
For the build-and-try workflow with Workshop below,
use `LXD 6.8 or later <https://canonical.com/lxd>`_, configured and running.

Install LXD if needed, then install SDKcraft:

.. code-block:: console

   sudo snap install --channel=6/stable lxd  # skip if LXD is already installed
   sudo snap install --classic sdkcraft

To get new features as soon as they land,
add ``--channel=latest/edge`` to the SDKcraft install command.

If an existing LXD installation needs updating:

.. code-block:: console

   sudo snap refresh --channel=6/stable lxd

Follow the `Workshop setup guide
<https://ubuntu.com/workshop/docs/tutorial/part-1-get-started/>`_
to configure LXD and install Workshop for trying SDKs locally.


Quick start
-----------

Create a directory for your SDK and initialize the project:

.. code-block:: console

   mkdir my-sdk
   cd my-sdk
   sdkcraft init

This creates ``sdkcraft.yaml`` together with hooks and tests.
Edit the definition to describe your SDK's software, platforms, and interfaces,
and add the hooks needed to set it up inside a workshop.

Build and package the SDK:

.. code-block:: console

   sdkcraft pack

The output is a ``.sdk`` artifact for each platform built.
For a complete worked example, follow the `SDK crafting tutorial
<https://ubuntu.com/workshop/docs/tutorial/part-4-craft-sdks/>`__.


Try and test locally
--------------------

Pack the SDK and copy it to Workshop's local try area:

.. code-block:: console

   sdkcraft try

The artifact is now available for local use with Workshop.
Follow `Build an SDK
<https://ubuntu.com/workshop/docs/how-to/develop-sdks/build-an-sdk/>`__
to launch a workshop with it and inspect how it behaves.

Run the SDK's Spread test suite, scaffolded by ``sdkcraft init``:

.. code-block:: console

   sdkcraft test

This packs the SDK and exercises it
in a separate test environment with Workshop installed.
Extend the scaffolded tests
to cover the tools and integrations your SDK provides.

To remove build artifacts before rebuilding:

.. code-block:: console

   sdkcraft clean


Publish and release
-------------------

Publishing makes an SDK available from the SDK Store.
With an Ubuntu One account, sign in and reserve your SDK's name:

.. code-block:: console

   sdkcraft login
   sdkcraft register my-sdk

Upload a tested artifact and release it to an initial channel.
Replace the example filename with the artifact produced by your build:

.. code-block:: console

   sdkcraft upload my-sdk_amd64_ubuntu@24.04.sdk --release latest/edge

List the uploaded revisions:

.. code-block:: console

   sdkcraft revisions my-sdk

When a revision is ready for stable use, release it to ``latest/stable``.
Replace ``<REVISION>`` with the revision number from the listing:

.. code-block:: console

   sdkcraft release my-sdk <REVISION> latest/stable

Workshop users can then select your SDK and its channel in their project definitions.
See `Publish an SDK
<https://ubuntu.com/workshop/docs/how-to/develop-sdks/publish-an-sdk/>`__
for the full publishing workflow.


Documentation
-------------

- `SDK crafting tutorial
  <https://ubuntu.com/workshop/docs/tutorial/part-4-craft-sdks/>`__:
  build your first SDK with a worked example.

- `Build an SDK
  <https://ubuntu.com/workshop/docs/how-to/develop-sdks/build-an-sdk/>`__:
  define, build, and exercise an SDK locally.

- `Publish an SDK
  <https://ubuntu.com/workshop/docs/how-to/develop-sdks/publish-an-sdk/>`__:
  distribute revisions through the SDK Store.

- `SDKcraft command reference
  <https://ubuntu.com/workshop/docs/reference/cli/sdkcraft/>`_:
  command usage and options.

- `Reference SDKs <https://github.com/canonical/reference-sdks>`_:
  examples of SDK implementations.

- `Workshop documentation <https://ubuntu.com/workshop/docs/>`_:
  the environments your SDKs become part of.


Community and support
---------------------

- `Code of conduct <https://ubuntu.com/community/docs/ethos/code-of-conduct>`_

- `Discourse <https://discourse.ubuntu.com/>`_

- `Product and documentation feedback <https://github.com/canonical/sdkcraft/issues/>`_


Contributions and license
-------------------------

To join the development effort, see `How to contribute
<https://ubuntu.com/workshop/docs/contributing/>`_.

When working on SDKcraft itself,
generate the project schema from the repository root:

.. code-block:: console

   uv run python sdkcraft/models/project.py

This uses the ``craft-application`` version locked in ``uv.lock``
to keep the generated schema aligned with the project's dependencies.

SDKcraft is released under the
`GPL-3.0 license <https://github.com/canonical/sdkcraft/blob/main/LICENSE>`_.
