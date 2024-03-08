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
comprise the majority of your daily needs with |project_markup|.

For more comprehensive details, explore the
:ref:`reference <ref_index>` and :ref:`explanation<exp_index>` sections.


.. attention::

   One technical detail before you start:
   currently, |project_markup| supports only :samp:`amd64`.


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

Build the :program:`sdkcraft` snap
from the |project_markup| source code on
`GitHub`_:

.. code-block:: console

   $ git clone git@github.com:canonical/sdkcraft.git  # or git clone https://github.com/canonical/sdkcraft.git
   $ cd sdkcraft
   $ sudo snap install snapcraft --classic
   $ snapcraft clean && snapcraft


Install the resulting :file:`.snap` file,
for example:

.. code-block:: console

   $ sudo snap install --dangerous --classic ./sdkcraft_0.1_amd64.snap


The snap installs the :program:`sdkcraft` CLI tool.
Make sure it runs:

.. code-block:: console

   $ sdkcraft --help


Prepare an SDK
--------------

Having installed |project_markup|,
use it to initialise, define and pack your first :ref:`SDK <exp_sdks>`.
Here, we'll build an SDK that installs a recent Python version in the workshop.


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
   despite being almost empty,
   it can already be built and published.

   However, let's make some extra steps
   to see what goes into an SDK.


#. Update the metadata in :file:`sdkcraft.yaml`;
   at the very least,
   customise its :samp:`name`, :samp:`summary` and :samp:`description`:

   .. code-block:: yaml
      :caption: sdkcraft.yaml
      :emphasize-lines: 1,4-6,15-18

      name: python
      base: ubuntu@22.04
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
        pythonhome:
          interface: content
          target: /usr/local/lib/python3.11


   The new section at the end defines a
   :ref:`content interface plug <exp_content_plug>`;
   think of it as a way to share the contents of :envvar:`$PYTHONHOME`
   between all workshops that include this SDK.


Add hooks
~~~~~~~~~

To prepare an SDK for action,
add some :ref:`hooks <exp_sdk_hooks>`
that run at different phases of the workshop's life cycle,
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
   installing prerequisites and preparing it for use.


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


   During a :command:`workshop refresh` operation:

   - The :file:`save-state` hook runs *before* the workshop is refreshed,
     storing the state of the SDK.

   - The :file:`restore-state` hook recovers the saved state
     *after* the workshop is successfully updated.

   - Both hooks use the :envvar:`$SDK_STATE_DIR` directory,
     exposed by the workshop to preserve the SDK's state.


   .. important::

      The SDK is also refreshed as a part of the workshop,
      so any breaking changes in its save-restore logic will cause an error.

#. Make all hooks executable so :program:`Workshop` can run them:

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
you need to publish it in the SDK Store
for use with :program:`Workshop`:

.. code-block:: console

   $ sdkcraft.publish ./python-sdk.sdk beta


This publishes the newly created SDK
under the :samp:`latest/beta` channel in the SDK Store,
from where it can be retrieved by the workshop as follows:

   .. code-block:: yaml
      :caption: .workshop.python.yaml
      :emphasize-lines: 4,5

      name: python
      base: ubuntu@22.04
      sdks:
        python-sdk:
          channel: latest/beta


Mind that the :samp:`base` of the workshop must match the SDK's :samp:`base`.

.. note::

   Currently, there's no way to reference local SDK packages in a workshop.


That was the last step of the tutorial;
you are now familiar with the essential operations |project_markup| provides
and have had your first taste of what it can accomplish for you.
