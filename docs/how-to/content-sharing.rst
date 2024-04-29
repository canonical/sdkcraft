.. _how_content_sharing:

How to share and persist content between host system and workshops
==================================================================

Consider this Docker command:

.. code-block:: console

   $ docker run --name share-example --entrypoint bash -it \
     -v ~/docker/kit/cache/Kit:/kit/cache:rw \
     -v ~/docker/cache/ov:/root/.cache/ov:rw \
     -v ~/docker/cache/pip:/root/.cache/pip:rw 
     -v ~/docker/data:/root/.local/share/ov/data:rw \
     -v ~/docker/documents:/root/Documents:rw \
     ...


And so on. An all-too-familiar sight, isn't it?
When running a sufficiently complex container,
you need to mount a lot of directories to make it work,
and the handling of these mounts both inside and outside
can quickly become a noticeable overhead.

Workshop addresses this issue by providing a way
to reuse and share content between workshops via SDKs
without handling the mounts manually.
Normally, all workshops are isolated from each other and the host system;
any data sharing needs to occur via the content interface.

To use it, your SDK need to define a content interface plug.
After that, the source directory on the host system will be mounted
to the target directory of all workshops that use the SDK.

.. note::

   Currently, there's no way to define the source directory at the SDK level;
   this is a feature that may be added in the future.


Having a content plug as a part of your SDK
for each notable content directory
facilitates data persistence and reuse;
any files created throughout one workshop's lifetime
will be available to all other workshops that use the same SDK,
as well as the same workshop after a refresh.


Persisting and reusing data between workshops
---------------------------------------------

This is the most straightforward scenario;
you choose the :samp:`content` interface and define the target directory
where the content will be mounted inside the workshop
per each directory you want to share.

.. code-block:: yaml
   :caption: sdkcraft.yaml

   name: data-science
   title: Data science SDK
   base: ubuntu@22.04
   summary: This SDK does some data science.
   description: |
     Besides doing actual data science,
     this SDK demonstrates content sharing and persistence between workshops
     by enabling two plugs that can store reusable data specific to the SDK.

   plugs:
     share-cache:
       interface: content
       target: /opt/cache

     share-build:
       interface: content
       target: /opt/build


Here, the SDK defines two content plugs.

At run-time, for each, Workshop will
automatically create and handle the source directory on the host,
while your SDK is responsible for using and reusing the target mount
via hooks and other features,
making appropriate use of both :samp:`target` directories
according to the SDK's purpose and logic.

.. code-block:: yaml
   :caption: .workshop.data.yaml

   name: data
   base: ubuntu@22.04
   sdks:
     data-science:
       channel: latest/stable


A world of difference with the Docker example, isn't it?

However, mind that changes to the content directory propagate between workshops,
affecting *all* workshops that use the same SDK.
This may not be too important when the shared directory is used as a scratchpad,
but it may become a problem if it's inadvertently used for sensitive data,
configuration files or build artefacts.

.. note::

   Currently, there is no consistency mechanism in place to prevent conflicts
   when multiple workshops try to write to the share.
   It's up to you, the SDK author,
   to suggest and implement an approach that prevents data corruption.


Sharing custom host content with a workshop
-------------------------------------------

One issue that the previous scenario doesn't address
is customising the source directory per each workshop.
The Docker command at the beginning of this page is an example of this;
it explicitly lists the host directories to mount along with their targets.

While |project_markup| doesn't provide a way
to define the source directory at the SDK level,
you can allow for greater flexibility by defining a *separate* SDK
whose sole purpose is to share any custom content with the workshop;
the users will then be able to mount their data directories at run-time
without interfering with the SDK-specific content.

Thus, instead of enabling any plugs in your main SDK that does all the work,
you can define a separate SDK that only enables the content plug:

.. code-block:: yaml
   :caption: sdkcraft.yaml

   name: data-sharing
   title: Content sharing SDK
   base: ubuntu@22.04
   summary: This SDK shares host files with the workshop.
   description: |
     this SDK demonstrates host content sharing with a workshop
     by enabling a content interface plug that can mount custom data.

   plugs:
     data-stash:
       interface: content
       target: /data-stash


That's it. The SDK doesn't need to do anything else;
to share custom content with a workshop,
the user only needs to add this SDK to the definition
beside the main logic
and refresh the workshop:

.. code-block:: yaml
   :caption: .workshop.data.yaml

   name: data
   base: ubuntu@22.04
   sdks:
     data-science:
       channel: latest/stable

     data-sharing:
       channel: latest/stable


If injecting custom data is a common use case for your SDK,
consider combining the two approaches;
this enables you to build more advanced logic
due to the fact that you always know the target mount point for the data.


See also
--------

Explanation:

- :ref:`exp_content_plug`
- :ref:`exp_sdk_hooks`