.. _exp_content_sharing:

Data persistence and sharing
============================

Consider this Docker command:

.. code-block:: console

   $ docker run --name share-example --entrypoint bash -it \
     -v ~/docker/kit/cache/Kit:/kit/cache:rw \
     -v ~/docker/cache/ov:/root/.cache/ov:rw \
     ...


An all-too-familiar sight, isn't it?
When running a sufficiently complex container,
you need to mount a lot of directories to make it work,
and the handling of these mounts both inside and outside
can quickly become an overhead.

|project_markup| addresses this issue by providing a way
to reuse and share content between individual workshops via SDKs
while keeping manual interventions to a necessary minimum.
Normally, all workshops are isolated from each other and the host system;
any data sharing needs to occur via the content interface.

To use it, your SDK defines a content interface plug.
When a workshop uses the SDK,
an auto-assigned, non-customisable source directory on the host
is mounted to the plug-defined target directory inside the workshop.
What's more, its content is preserved during refresh operations.
Thus, |project_markup| enables SDK data persistence and reuse
*inside* individual workshops.

It's important to note, though,
that files created at the plug's target location by any means
are only accessible to the workshop
that this specific auto-assigned source directory is mounted to.
Other workshops, even if they use the same SDK,
cannot access these files and do not share them;
their source directories are different.


Persisting and reusing data between workshops
---------------------------------------------

This is the most straightforward scenario;
you use the :samp:`content` interface
to define the target directory
where the content will be mounted inside the workshop
per each directory you want to preserve during the workshop's lifetime.

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


Here, the SDK defines two content plugs;
for each one,
:program:`Workshop` creates a source directory on the host at run-time.
Both :samp:`target` directories inside the workshop
can be put to use by the SDK-specific logic
implemented via SDK hooks and other features,
or the workshop user can manipulate them directly
with :command:`workshop shell` and similar commands.

Here's a corresponding workshop definition:

.. code-block:: yaml
   :caption: .workshop.data.yaml

   name: data
   base: ubuntu@22.04
   sdks:
     data-science:
       channel: latest/stable


However, mind that changes to the content directory
do not propagate between workshops;
nor can you pre-define the default host location
that :program:`Workshop` mounts to the target.


Sharing custom host content with a workshop
-------------------------------------------

One issue that the previous scenario doesn't address
is customising the source directory of a workshop.
The :command:`docker run` sample at the start exemplifies this approach;
it explicitly lists the host directories to mount to respective targets.

This can be achieved in :program:`Workshop` as well,
and the :command:`workshop remount` command is the key to it:

.. code-block:: console

   $ workshop remount data/data-science:share-cache ~/.local/cache/


This mounts a specific source location on the host, :file:`~/.local/cache/`,
to the target directory of the :samp:`share-cache` content interface plug
under the :samp:`data-science` SDK in the :samp:`data` workshop defined above.

If that's not the usage you intended for this specific plug,
but you still need to share arbitrary data with the workshop,
you can add a designated content interface plug for data sharing
or even define a *separate* SDK for this purpose;
the users will then be able to mix and match it with other SDKs
to avoid interfering with the SDK-specific content in their workshops.

Thus, instead of messing with the plugs in your :samp:`data-science` SDK,
define a separate SDK that only enables a plug for sharing data:

.. code-block:: yaml
   :caption: sdkcraft.yaml

   name: data-sharing
   title: Content sharing SDK
   base: ubuntu@22.04
   summary: This SDK shares host files with the workshop.
   description: |
     This SDK demonstrates host content sharing with a workshop
     by enabling a content interface plug that can mount custom data.

   plugs:
     data-stash:
       interface: content
       target: /data-stash


It doesn't need to do anything else;
to share custom content with a workshop,
the user only needs to add this SDK to the workshop definition
beside other SDKs that do the actual work and refresh the workshop:

.. code-block:: yaml
   :caption: .workshop.data.yaml

   name: data
   base: ubuntu@22.04
   sdks:
     data-science:
       channel: latest/stable

     data-sharing:
       channel: latest/stable


.. code-block:: console

   $ workshop refresh data


Sharing content between workshops
---------------------------------

The last issue left to address is the way to share data *between* workshops,
as opposed to persisting anything *inside* them.
Again, this can be achieved with :command:`workshop remount`.
Suppose you have two workshops, :samp:`data1` and :samp:`data2`,
each using the :samp:`data-science` SDK. This does the trick:

.. code-block:: console

   $ workshop remount data1/data-science:share-cache ~/.local/cache/
   $ workshop remount data2/data-science:share-cache ~/.local/cache/


The commands mount a single location on the host, :file:`~/.local/cache/`,
to the target directory of the :samp:`share-cache` plug under *each* workshop.
The data stored there is now accessible to them both;
they can read and write to it as they please,
and the rest is up to you and your SDK logic.


See also
--------

Explanation:

- :ref:`exp_content_interface`
- :ref:`exp_sdk_interfaces`