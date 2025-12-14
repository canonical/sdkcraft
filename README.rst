SDKcraft
========

.. warning::

   SDKcraft is currently an internal Canonical project.
   All code, documentation, and materials in this repository
   are company-private and must not be shared outside Canonical
   without prior authorization.

   Do not redistribute or discuss this content or the project externally
   (at public forums, in social media, with customers)
   until an official public release is announced.


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

Test your SDK in a clean environment:

.. code-block:: console

   sdkcraft try

Clean build artifacts:

.. code-block:: console

   sdkcraft clean

Publish your SDK to the SDK Store:

.. code-block:: console

   sdkcraft.publish ./my-sdk.sdk latest/edge


Installation
------------

SDKcraft is supported on Ubuntu and other ``snap``-enabled Linux distributions.

Authenticate to the Snap Store and install the snap
using the `--classic <https://snapcraft.io/docs/install-modes>`_ option:

.. code-block:: console

   sudo snap login
   sudo snap install --classic sdkcraft


Alternatively, you can download the latest SDKcraft snap from the
`Releases <https://github.com/canonical/sdkcraft/releases/>`_
page on GitHub and install it, using the options
`--dangerous <https://snapcraft.io/docs/install-modes>`_
and
`--classic <https://snapcraft.io/docs/install-modes>`_,
for example:

.. code-block:: console

   sudo snap install --dangerous --classic ./sdkcraft_0.1.12_amd64.snap


Prerequisites
~~~~~~~~~~~~~

SDKcraft requires
`LXD 6.3+ <https://canonical.com/lxd>`_
for low-level operation.

If the ``snap install`` command reports an issue with LXD,
install a recent LXD version with ``snap``:

.. code-block:: console

   sudo snap install --channel=6/stable lxd  # to install
   sudo snap refresh --channel=6/stable lxd  # to update


Documentation
-------------

Refer to `Part 4 of the tutorial
<https://canonical-workshop.readthedocs-hosted.com/stable/tutorial/part-4-craft-sdks/>`_
in our docs for a detailed introduction to SDKcraft.

To know more about `Workshop <https://github.com/canonical/workshop/>`_ in general,
jump straight to the
`documentation home page <https://canonical-workshop.readthedocs-hosted.com/>`_.

Generate the project schema JSON:

.. code-block:: console

   uv run python sdkcraft/models/project.py

This uses the exact version of ``craft-application`` locked in ``uv.lock``,
ensuring schema consistency.


Community and Support
---------------------

Use the following resources for communication, support, and feedback:

- `Code of conduct <https://ubuntu.com/community/ethos/code-of-conduct>`__

- `Pulse reviews on Discourse <https://discourse.canonical.com/c/engineering/sdk/34>`__

- `Mattermost channel <https://chat.canonical.com/canonical/channels/sdk>`__

- `Product and documentation feedback <https://github.com/canonical/sdkcraft/issues/>`__


Contributions
-------------

To join the development effort, see `How to contribute
<https://canonical-workshop.readthedocs-hosted.com/latest/contributing/>`_.
