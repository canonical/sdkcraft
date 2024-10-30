:hide-toc:

.. _exp_sdk_parts:

SDK parts
=========

Parts provide a way to modularise the SDK and manage its dependencies,
ultimately making it easier to maintain and update
by separating its deployment into sourcing, building and staging phases.


Summary
-------

Parts can be thought of as the building blocks of an SDK.
Each part in the :ref:`definition <exp_sdk_definition>`
encapsulates a different aspect of the SDK
and focuses on a specific feature or resource;
these can be libraries, binaries, or configuration files.

A part defines a number of preset attributes and life cycle stages in YAML;
|project_markup| executes these definitions stage by stage
and iteratively resolves any dependencies between parts.
Eventually, this results in a uniform SDK,
ready for publishing and installation;
such SDKs arrive to the users pre-built,
allowing to factor out build activities from :ref:`SDK hooks <exp_sdk_hooks>`
that run inside the workshop.


Implementation notes
--------------------

Full disclosure: |project_markup| borrows the
`Craft Parts <https://github.com/canonical/craft-parts/>`_
mechanism from the upstream
`Craft Application <https://github.com/canonical/craft-application/>`_
project,
ultimately sharing it with such tools as
`Snapcraft <https://snapcraft.io/docs/>`_
and
`Charmcraft <https://juju.is/docs/sdk/charmcraft/>`_,
so general approaches that work for any of those will apply here.

Aside from not yet allowing :samp:`stage-packages` and :samp:`stage-snaps`,
|project_markup| doesn't further limit or expand the parts functionality.
However, be aware of the requirements and limitations
that the upstream project places on what's available
for a given base, plugin, source and so on.

A detailed explanation is available in the corresponding Craft Parts
`documentation section
<https://canonical-craft-parts.readthedocs-hosted.com/en/latest/explanation/index.html>`_.


Case study: Vitis AI
--------------------

To explore what parts can do for you, we'll use the `AMD Vitis AI
<https://github.com/Xilinx/Vitis-AI-Tutorials>`_ SDK (:samp:`amd-vitis-ai`)
as an example.
It relies on parts to gradually build an SDK
that's ready to use immediately after download.
The only task left after the SDK is extracted
is adding a symbolic link to its location within the workshop,
which is handled by the :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`.

The structure and layout of parts are mostly flexible,
but the key is to ensure they interact well with each other
and align with the overall `life cycle
<https://craft-parts.readthedocs.io/en/latest/explanation/lifecycle.html>`_.

.. dropdown:: :samp:`download-chroot-base`

   .. literalinclude:: parts/sdkcraft.yaml
      :language: yaml
      :start-after: [download-chroot-base-start]
      :end-before: [download-chroot-base-end]


This part downloads and sets up a basic Ubuntu root file system (chroot).
The properties referenced here demonstrate how parts work,
so let's discuss them in more detail:

- The :samp:`plugin` property is set to :samp:`nil`,
  indicating that the part doesn't rely on a specific build tool,
  but instead provides generic steps.
  In your own definition, you can choose between a `range of options
  <https://craft-parts.readthedocs.io/en/latest/reference/part_properties.html#plugin>`_
  depending on the tools needed to build the SDK.

- The `build-packages
  <https://craft-parts.readthedocs.io/en/latest/reference/part_properties.html#build-packages>`_
  property lists a single prerequisite package, :samp:`wget`.
  This package will be installed using the default package manager
  of the SDK's :samp:`base` system.

- The `override-build
  <https://craft-parts.readthedocs.io/en/latest/reference/part_properties.html#override-build>`_
  property provides shell commands to perform SDK-specific actions.
  Here, they fetch a tarball for the architecture set by :samp:`platforms`,
  extract it into a directory called :file:`sysroot`,
  and copy it to the staging area
  defined by the :envvar:`$CRAFT_STAGE` environment variable,
  which contains the absolute path to where the SDK files should be staged.


Overall, this step ensures that the necessary base environment is available
before proceeding to additional setup,
such as configuring package management and adding external repositories.

.. dropdown:: :samp:`prepare-chroot`

   .. literalinclude:: parts/sdkcraft.yaml
      :language: yaml
      :start-after: [prepare-chroot-start]
      :end-before: [prepare-chroot-end]


This step builds on the base chroot environment
created by :samp:`download-chroot-base`,
listed as a prerequisite in the `after
<https://craft-parts.readthedocs.io/en/latest/reference/part_properties.html#after>`_
property.
The other properties used here are the same as above.

The commands set up essential system mounts for
:file:`/dev/`, :file:`/proc/`, :file:`/sys/` and other directories
necessary for package management operations within the chroot.
A DNS configuration is copied to enable network access inside the chroot.
Afterwards, the part updates the package index
and installs packages
such as :samp:`software-properties-common` and :samp:`gnupg`
to allow further package management tasks.
Finally, it performs a system upgrade within the chroot
before unmounting the directories and restoring the environment.


.. dropdown:: :samp:`xilinx-sdk`

   .. literalinclude:: parts/sdkcraft.yaml
      :language: yaml
      :start-after: [xilinx-sdk-start]
      :end-before: [xilinx-sdk-end]


The properties used here are similar to those above.
Overall, this part focuses on preparing the chroot environment for development.

Building on the prepared chroot,
the :samp:`override-build` script mounts the required file systems
and installs a list of essential development packages inside the chroot,
ensuring that all dependencies are present.
An important element is the :samp:`make_all_links_relative()` function,
which converts absolute symbolic links into relative ones,
improving the portability of the resulting setup.
Finally, the chroot is properly shut down
by unmounting system directories and cleaning up.

.. dropdown:: Complete :file:`sdkcraft.yaml`

   .. literalinclude:: parts/sdkcraft.yaml
      :language: yaml


See also
--------

Explanation:

- :ref:`exp_sdks`


Reference:

- :ref:`ref_sdk_parts`
