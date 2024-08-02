.. _tutorial:

Tutorial
========

This is a practical introduction
that takes you on a tour
of the essential |project_markup| activities.

Here, you will initialise, define, pack and publish an :ref:`SDK <exp_sdks>`:
a set of hooks, interfaces and parts that is bundled into a single package,
suitable for use with `Workshop`_.
The commands you're about to run
cover most of your daily needs with |project_markup|.

For more details, see the
:ref:`reference <ref_index>` and :ref:`explanation <exp_index>` sections.


Check prerequisites
-------------------

|project_markup| requires
`LXD <https://canonical.com/lxd>`_
for low-level operation,
using its
`REST API <https://documentation.ubuntu.com/lxd/en/latest/restapi_landing/>`_
to configure and build the SDKs.

First, install and
`initialise <https://documentation.ubuntu.com/lxd/en/latest/howto/initialize/>`_
LXD.
It's available as a snap:

.. tabs::
   .. group-tab:: Using :program:`snap`

      .. code-block:: console

         $ sudo snap install lxd
         $ sudo lxd init --auto


   .. group-tab:: Other ways

      See the available installation options in
      `LXD documentation
      <https://documentation.ubuntu.com/lxd/en/latest/installing/>`_.


Next, ensure the
`LXD daemon
<https://documentation.ubuntu.com/lxd/en/latest/explanation/lxd_lxc/#lxd-daemon>`_
is enabled and running:

.. tabs::
   .. group-tab:: Using :program:`snap`

      .. code-block:: console

         $ sudo snap start --enable lxd.daemon
         $ snap services lxd.daemon

   .. group-tab:: Other ways

      Refer to
      `LXD documentation
      <https://documentation.ubuntu.com/lxd/en/latest/installing/>`_
      and your distribution's manuals for guidance.


Install |project_markup|
------------------------

Download the latest snap from the
`Releases <https://github.com/canonical/sdkcraft/releases/>`_
page on GitHub and install it,
using the options
`--dangerous <https://snapcraft.io/docs/install-modes#heading--dangerous>`_
and
`--classic <https://snapcraft.io/docs/install-modes#heading--confinement>`_,
for example:

.. code-block:: console

   $ sudo snap install --dangerous --classic ./sdkcraft_0.1_amd64.snap


The snap installs the :program:`sdkcraft` CLI tool.
Make sure it runs:

.. code-block:: console

   $ sdkcraft --help


Prepare an SDK
--------------

Once you have installed |project_markup|,
use it to initialise, define and pack your first :ref:`SDK <exp_sdks>`.
Here, we'll build an SDK that installs a version of Python in the workshop.


.. _tut_init:

Define
~~~~~~

#. Create a directory
   named :file:`python-sdk`:

   .. code-block:: console

      $ mkdir python-sdk
      $ cd python-sdk


   It will contain your :ref:`SDK definition <exp_sdk_definition>`
   and other source files.


#. Initialise the SDK directory:

   .. code-block:: console

      $ sdkcraft init

   This command creates a template definition file
   named :file:`sdkcraft.yaml`;
   although it's almost empty,
   it's ready to be built and published.

   However, let's take a few extra steps
   to explore what can go into an SDK.


#. Update the metadata in :file:`sdkcraft.yaml`;
   at the very least,
   adjust its :samp:`name`, :samp:`summary` and :samp:`description`:

   .. code-block:: yaml
      :caption: sdkcraft.yaml
      :emphasize-lines: 1,4-6

      name: python
      base: ubuntu@24.04
      version: '0.1'
      summary: Python SDK
      description: |
        This is my Python SDK's description.
      license: GPL-3.0
      platforms:
        amd64:

      parts:
        my-part:
          plugin: nil


.. _tut_content_interface:

Add interface plugs
~~~~~~~~~~~~~~~~~~~

In |project_markup|,
:ref:`interfaces <exp_sdk_interfaces>` provide a controllable way
of exposing the resources of the host system to the workshops,
and you can use them in a variety of ways
to extend the functionality of your SDK.

Suppose you want to preserve the installed Python packages
when a workshop using your SDK is rebuilt from scratch.
You can use a :ref:`content interface <exp_content_interface>` plug:
it mounts a host directory to a target directory in the workshop,
so that the files remain on the host.

Open :file:`sdkcraft.yaml` again
and add a plug named :samp:`packages` to the :samp:`plugs` section:

   .. code-block:: yaml
      :caption: sdkcraft.yaml
      :emphasize-lines: 15-18

      name: python
      base: ubuntu@24.04
      version: '0.1'
      summary: Python SDK
      description: |
        This is my Python SDK's description.
      license: GPL-3.0
      platforms:
        amd64:

      parts:
        my-part:
          plugin: nil

      plugs:
        packages:
          interface: content
          target: /usr/local/lib/python3.11


Now, when a workshop using this SDK is started,
:program:`Workshop` will map the plug's :samp:`target` in the workshop
to a host directory that will be automatically created
and maintained between refresh operations.

.. note::

   You can't explicitly set the host directory here;
   this prevents SDKs from accessing any arbitrary data on the host file system.
   However, users who add your SDK to their workshops
   will be able to remount the plug elsewhere at run-time.


Add hooks
~~~~~~~~~

To prepare an SDK for use,
add some :ref:`hooks <exp_sdk_hooks>`
that run at different stages of the workshop's life cycle,
preparing the SDK for use or preserving its state during updates.

#. Under :file:`python-sdk/`,
   create a subdirectory
   named :file:`hooks/`:

   .. code-block:: console

      $ mkdir hooks
      $ cd hooks

   This directory stores all the hooks for an SDK.

#. Under :file:`python-sdk/hooks/`,
   create a file
   named :file:`setup-base`:

   .. code-block:: shell
      :caption: setup-base

      #!/usr/bin/bash

      # NOTE: we use apt-get instead of apt for non-interactive package installation.
      # apt will prompt services restart for some of the packages below which will
      # make the SDK installation stall forever.

      # Update package list
      apt-get -y update

      # Ensure the Ubuntu Universe repos are enabled
      apt-get -y install software-properties-common
      add-apt-repository universe

      # Install Python 3.11
      apt-get -y update
      apt-get -y install python3.11 python3.11-dev python3.11-venv

      # Create working directory
      sudo -u workshop -- mkdir -p /home/workshop/my_python_work/


   It runs when the workshop is launched or refreshed,
   installing the prerequisites and preparing it.


#. Also under :file:`python-sdk/hooks/`,
   create two files
   named :file:`save-state` and :file:`restore-state`:

   .. code-block:: shell
      :caption: save-state

      #!/usr/bin/bash
      rsync -a /home/workshop/my_python_work/ $SDK_STATE_DIR


   .. code-block:: shell
      :caption: restore-state

      #!/usr/bin/bash
      rsync -a $SDK_STATE_DIR/ /home/workshop/my_python_work


   During a :command:`workshop refresh` operation:

   - The :file:`save-state` hook runs *before* the workshop is refreshed,
     saving the state of the SDK.

   - The :file:`restore-state` hook recovers the state
     *after* the workshop has been successfully updated.

   - Both hooks use the workshop's :envvar:`$SDK_STATE_DIR` directory
     to store the SDK state.


   .. important::

      The SDK is also refreshed as a part of the workshop,
      so any breaking changes in its save-restore logic will cause an error.


#. Finally,
   create a hook
   named :file:`check-health`:

   .. code-block:: shell
      :caption: check-health

      #!/usr/bin/bash
      python3 -c "import os" || workshopctl set-health --code=installation-fails error "Python 3 installation fails"


   It checks whether the Python installation is actually functional
   and reports an error via :ref:`workshopctl <exp_workshopctl>` if it's not.


#. Make all hooks executable so that :program:`Workshop` can run them:

   .. code-block:: console

      $ cd ..  # back to python-sdk/
      $ chmod +x hooks/*


Package
~~~~~~~

Under :file:`python-sdk/`, run:

.. code-block:: console

   $ sdkcraft pack


This creates the :file:`python-sdk.sdk` file,
which contains the SDK metadata, hooks and other components.


.. _tut_publish:

Publish the SDK
---------------

When an SDK is ready and packed,
you need to publish it to the SDK Store
for use with :program:`Workshop`:

.. code-block:: console

   $ sdkcraft.publish ./python-sdk.sdk beta


This publishes the newly created SDK
under the :samp:`latest/beta` channel in the SDK Store,
where it can be accessed by :program:`Workshop` as follows:

   .. code-block:: yaml
      :caption: .workshop.python.yaml
      :emphasize-lines: 4,5

      name: python
      base: ubuntu@24.04
      sdks:
        python-sdk:
          channel: latest/beta


Mind that the :samp:`base` of the workshop must match the SDK :samp:`base`.

.. note::

   Currently, there's no way to reference local SDK packages in a workshop.


This was the last step of the tutorial;
you are now familiar with the basic operations |project_markup| provides
and have had your first taste of what it can do for you.
