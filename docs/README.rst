SDKcraft
========

.. image:: https://readthedocs.com/projects/canonical-sdkcraft/badge/?version=latest&token=3b181ca357f8968cf17221c27353866e63087d6b2f1ced225db4978acb38c0a7
   :target: https://canonical-sdkcraft.readthedocs-hosted.com/en/latest/?badge=latest
   :alt: Documentation Status

**A tool that packages and publishes SDKs to be used with Workshop,
a related user-facing product**.

**Define your SDK in simple YAML**.
Next, SDKcraft instantiates the definition
and snapshots the resulting SDK into a tarball,
which you can then publish to be retrieved and used with Workshop.

**Describe your project's ins and outs in a consistent manner**.
Use a common, instantly recognisable paradigm
to make all aspects of your setup and usage explicit.
SDKcraft provides a uniform way to bake in your domain expertise
instead of leaving the users to figure everything out by trial and error.

**For those who maintain and distribute complex SDKs and frameworks**.
Many software domains have less-than-trivial project layouts
that require significant effort to set up and support.
That’s where SDKcraft gives you an edge
by making your product easier to package, distribute, install and use.


Getting Started
---------------

Follow the sections below
or refer to the
`Tutorial
<https://canonical-sdkcraft.readthedocs-hosted.com/en/latest/tutorial/>`_
in our docs for a more detailed introduction to SDKcraft.

To know more about `Workshop <https://github.com/canonical/workshop>`_,
the user-facing counterpart to SDKcraft,
start with the `Tutorial
<https://canonical-workshop.readthedocs-hosted.com/en/latest/tutorial/>`_.


------------
Installation
------------

SDKcraft requires
`LXD <https://canonical.com/lxd>`_
for low-level operation:

.. code-block:: console

   sudo snap install lxd
   sudo lxd init --auto


Build and install the ``sdkcraft`` snap, for example:

.. code-block:: console

   git clone git@github.com:canonical/sdkcraft.git  # or git clone https://github.com/canonical/sdkcraft.git
   cd sdkcraft
   sudo snap install snapcraft --classic
   snapcraft clean && snapcraft
   sudo snap install --dangerous --classic ./sdkcraft_0.1_amd64.snap


Packing an SDK
--------------

Browse to the directory with the prepared SDK files
and initialise an SDK:

.. code-block:: console

   cd readme-sdk
   sdkcraft init


#. Update the metadata in :file:`sdkcraft.yaml`;
   at the very least,
   customise its :samp:`name`, :samp:`summary` and :samp:`description`:

   .. code-block:: yaml
      :caption: sdkcraft.yaml
      :emphasize-lines: 1,4-6,15-18

      name: readme-sdk
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


Finally, pack the SDK:

.. code-block:: console

   sdkcraft pack


Publishing the SDK
------------------

An SDK can be released on the `SDK Store
<https://github.com/canonical/sdk-store>`_.
The store is currently on public GCS storage,
and publishers need write permissions.
To release an SDK in the ``edge`` track of the latest channel:

.. code-block:: console

   sdkcraft.publish ./readme-sdk.sdk edge


Testing
-------

SDKcraft uses `craftcraft
<https://github.com/canonical/craftcraft/blob/main/HACKING.rst>`_'s
testing workflow based on `tox <https://tox.wiki/>`_:

.. code-block:: console

   python --version                   # Needs Python 3.10+
   sudo snap install shellcheck
   sudo snap install ruff             # Needs external linters
   pip install tox
   tox


To run end-to-end tests and integration tests with
`Spread <https://github.com/snapcore/spread>`_:

.. code-block:: console

   go install github.com/snapcore/spread/cmd/spread@latest
   spread
