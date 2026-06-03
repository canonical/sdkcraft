SDKcraft
========

.. image:: https://github.com/canonical/sdkcraft/actions/workflows/qa.yaml/badge.svg
   :target: https://github.com/canonical/sdkcraft/actions/workflows/qa.yaml
   :alt: QA Status

SDKcraft is a tool that packages and publishes SDKs to be used with
`Workshop <https://github.com/canonical/workshop>`_,
a related user-facing product.
SDKcraft solves the essential problem of creating reproducible, distributable
development environments by allowing developers to define, build, and package
complete SDKs as singular installable units.

SDKcraft is useful for developers who need to distribute complex development
toolchains, maintainers who want to ensure consistent development environments
across teams, and organizations looking to streamline toolchain distribution and
management.


Using SDKcraft
--------------

Here are the core SDKcraft commands that demonstrate the essence of the tool.

Initialize a new SDK project:

.. code-block:: console

   sdkcraft init

Build and package your SDK:

.. code-block:: console

   sdkcraft pack

Pack the SDK and stage it in the Workshop try area for manual try-out:

.. code-block:: console

   sdkcraft try

Run the SDK's spread suite (scaffolded by ``sdkcraft init``) against the
freshly packed artifact in a clean LXD container:

.. code-block:: console

   sdkcraft test

Clean build artifacts:

.. code-block:: console

   sdkcraft clean

Publishing flows through the SDK Store.
Authenticate once, reserve the SDK name,
then upload a revision and release it to a channel:

.. code-block:: console

   sdkcraft login
   sdkcraft register <NAME>
   sdkcraft upload <NAME>_<ARCH>_<BASE>.sdk --release latest/edge

Promote an existing revision between channels with ``sdkcraft release``:

.. code-block:: console

   sdkcraft revisions <NAME>
   sdkcraft release <NAME> <REVISION> latest/stable


Installation
------------

SDKcraft is supported on Ubuntu and other ``snap``-enabled Linux distributions.

Install the snap using the
`--classic <https://snapcraft.io/docs/install-modes>`_ option:

.. code-block:: console

   sudo snap install --classic sdkcraft


Prerequisites
~~~~~~~~~~~~~

SDKcraft requires
`LXD 6.6 or later <https://canonical.com/lxd>`_
for low-level operation.

If the ``snap install`` command reports an issue with LXD,
install a recent LXD version with ``snap``:

.. code-block:: console

   sudo snap install --channel=6/stable lxd  # to install
   sudo snap refresh --channel=6/stable lxd  # to update


Documentation
-------------

Refer to `Part 4 of the tutorial
<https://ubuntu.com/workshop/docs/tutorial/part-4-craft-sdks/>`_
in our docs for a detailed introduction to SDKcraft;
for more detailed guidance,
see the `Build an SDK <https://ubuntu.com/workshop/docs/how-to/develop-sdks/build-an-sdk/>`__
and
`Publish an SDK <https://ubuntu.com/workshop/docs/how-to/develop-sdks/publish-an-sdk/>`__
how-to guides.

For reference examples of SDK implementation, see the
`reference SDKs repository <https://github.com/canonical/reference-sdks>`__.

To know more about `Workshop <https://github.com/canonical/workshop/>`_ in general,
jump straight to the
`documentation home page <https://ubuntu.com/workshop/docs/>`_.

Generate the project schema JSON:

.. code-block:: console

   uv run python sdkcraft/models/project.py

This uses the exact version of ``craft-application`` locked in ``uv.lock``,
ensuring schema consistency.


Community and Support
---------------------

Use the following resources for communication, support, and feedback:

- `Code of conduct <https://ubuntu.com/community/docs/ethos/code-of-conduct>`__

- `Discourse <https://discourse.ubuntu.com/>`__

- `Product and documentation feedback <https://github.com/canonical/sdkcraft/issues/>`__


Contributions
-------------

To join the development effort, see `How to contribute
<https://ubuntu.com/workshop/docs/contributing/>`_.
