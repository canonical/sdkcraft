SDKcraft
========

A tool to create SDKs for [Workshop](https://github.com/canonical/workshop).


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
