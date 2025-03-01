SDKcraft
========

**A tool that packages and publishes SDKs to be used with Workshop,
a related user-facing product**.


Getting Started
---------------

Follow the sections below
or refer to the
`how-to guide
<https://canonical-workshop.readthedocs-hosted.com/en/latest/how-to/use-sdkcraft/>`_
in our docs for a more detailed introduction to SDKcraft.

To know more about `Workshop <https://github.com/canonical/workshop/>`_,
the user-facing counterpart to SDKcraft,
start with its own `Tutorial
<https://canonical-workshop.readthedocs-hosted.com/en/latest/tutorial/>`_.


Installation
~~~~~~~~~~~~

SDKcraft requires
`LXD 5.21+ <https://canonical.com/lxd>`_
for low-level operation:

.. code-block:: console

   sudo snap install lxd
   sudo lxd init --auto


Download the latest snap from the
`Releases <https://github.com/canonical/sdkcraft/releases/>`_
page on GitHub and install it,
using the options
`--dangerous <https://snapcraft.io/docs/install-modes>`_
and
`--classic <https://snapcraft.io/docs/install-modes>`_,
for example:

.. code-block:: console

   sudo snap install --dangerous --classic ./sdkcraft_0.1.5_amd64.snap


Packing an SDK
--------------

#. Browse to the directory with the prepared SDK files
   and initialise an SDK:

   .. code-block:: console

      cd readme
      sdkcraft init


#. Update the metadata in ``sdkcraft.yaml``,
   at least its ``name``, ``summary`` and ``description``:

   .. code-block:: yaml

      name: readme
      base: ubuntu@22.04
      version: '0.1'
      summary: Readme SDK
      description: |
        This is my Readme SDK's description.
      license: GPL-3.0
      platforms:
         amd64:

      parts:
        my-part:
          plugin: nil


#. Under ``readme/``, run:

   .. code-block:: console

      $ sdkcraft


   This builds all SDK parts
   defined in the ``sdkcraft.yaml`` file,
   e.g. pulling source code, applying patches, configuring and compiling it
   according to the part definition.

   After the build, SDKcraft packs the SDK.
   The resulting ``readme.sdk`` file contains the build artefacts
   along with SDK metadata, hooks and other components.


Publishing the SDK
------------------

An SDK can be released on the `SDK Store
<https://github.com/canonical/sdks>`_.
The store is currently on public GCS storage,
and publishers need write permissions.
To release an SDK in the ``edge`` track of the latest channel:

.. code-block:: console

   sdkcraft.publish ./readme.sdk latest/edge


Testing
-------

To run a local test from the source code, use the destructive mode:

.. code-block:: console

   python -m sdkcraft --destructive-mode

It allows injecting the ``sdkcraft`` snap from the host instead of the Snap Store,
providing a faster way to run simple local tests during development,
but isn't enough for an end-to-end test.

For a sufficient end-to-end test,
the snap should be packed and installed before running.
Install our fork of `Spread <https://github.com/snapcore/spread>`_ to run it:

.. code-block:: console

   git clone https://github.com/dmitry-lyfar/spread
   cd spread
   go install ./...

   cd ../sdkcraft
   spread
