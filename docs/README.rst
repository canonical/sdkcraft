SDKcraft
========

A tool to create SDKs for `Workshop <https://github.com/canonical/workshop>`_.


Installing
----------

.. code:: console

   $ git clone https://github.com/canonical/sdkcraft
   $ cd sdkcraft
   $ snapcraft
   $ sudo snap install --dangerous --classic sdkcraft_<REVISION>_amd64.snap


Running
-------

In the directory with the prepared SDK files:

.. code:: console

   $ sdkcraft init
   $ sdkcraft pack

Publishing
----------

An SDK can be published in the `SDK Store
<https://github.com/canonical/sdk-store>`_. Currently, the store is hosted on
public GCS storage, and a publisher must have writing permissions to it. To
publish an SDK in a specified track of the latest channel, run:

.. code:: console

   $ sdkcraft.publish ./my-sdk.sdk edge
