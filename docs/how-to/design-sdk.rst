.. _how_create_ros2_sdk:

How to design an SDK
====================

For a practical example of SDK design and layout,
let's see how an SDK for
`ROS 2
<https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html>`_
that we have published in our SDK Store
is structured.

.. note::

   This guide assumes that you already have |project_markup|
   :ref:`installed <tutorial>` and know how to use it.
   Also, our ROS 2 SDK is currently based on the :samp:`jazzy` distribution;
   adapt these steps for other distributions as needed.


Define the SDK
--------------

Here's the entire SDK definition:

.. literalinclude:: design-sdk/sdkcraft.yaml
   :language: yaml


Looks great, but what does it do?
Let's review the less trivial sections:

.. list-table::
   :widths: 1 3

   * - :samp:`platform`
     - The SDK targets both :samp:`amd64` and :samp:`arm64`.
       Currently, `Workshop`_ is available only for :samp:`amd64`,
       but this is subject to change.

   * - :samp:`parts`
     - This is essentially a stub;
       currently, :program:`Workshop` doesn't implement any :samp:`parts`
       mechanisms similar to what's available in snaps, for example.
       Again, this is subject to change,
       and many actions that we do with :ref:`hooks <how_ros2_sdk_hooks>`
       will eventually move here.

   * - :samp:`plugs`
     - This section defines two content plugs and a GPU plug.

       The first content plug, :samp:`ros-cache`, maps ROS 2 configuration
       to a host directory to preserve it between refreshes.
       The second one, :samp:`colcon-cache`,
       is where the build artefacts will end up at run-time,
       so the build cache can be persisted and reused.

       The GPU plug provides GPU pass-through for the SDK.


Summarily, the definition builds upon :program:`Workshop`'s capabilities,
persisting the important reusable parts of the setup on the host
and making its GPU capabilities directly available.

However, to make this definition work,
the SDK should be installed to target the two content directories;
currently, this is achieved with SDK hooks.


.. _how_ros2_sdk_hooks:

Define the hooks
----------------

The design of the SDK doesn't require preserving any state between refreshes;
everything is cached on the host instead.
Thus, the :samp:`save-state` and :samp:`restore-state` hooks aren't used,
so we only have to define the :samp:`setup-base` hook.

The entire source can be found :download:`here <design-sdk/setup-base.txt>`;
let's focus on the more important sections and what they do.

The key idea behind the design is two-fold.
Aside from installing the prerequisites, the hook does two important things:

- Points the build configuration to the directory set for :samp:`colcon-cache`
- Looks up project dependencies in the :samp:`/project/` directory,
  assuming the project sources are already mapped there,
  and installs them automatically

Both should simplify reuse and reentry for SDK users;
we'll discuss their operation in detail below.


Path variables
~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 5-10


Defines various environment-specific variables,
including paths for the workspace, configuration files,
and the ROS 2 distribution (:samp:`jazzy`).


Package management setup
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 16-24


Updates the package list and ensures necessary tools
(:program:`software-properties-common` and :program:`curl`)
are installed and the :samp:`universe` repository is enabled.

With this, we can enable the specific repository we need.

Setup ROS 2 GPG key and repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 26-34


Downloads the ROS 2 GPG key and adds the ROS 2 repository
to the sources list for package management;
this is done in a manner typical of Ubuntu-based installations
(mind that we target :samp:`ubuntu@24.04` as :samp:`base`).


Install ROS 2 development tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 26-34


Using the repository configured earlier,
this installs ROS 2 development tools and additional :program:`colcon` tools
for building and managing packages (this time, in the sense of ROS 2).


Setup minimal ROS 2 workspace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 48-52


Installs minimal workspace packages and tools
for running and launching ROS 2 nodes.


Update :file:`.bashrc` for ROS 2 and :program:`colcon`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 54-70


Adds lines to the :file:`.bashrc` file
to source ROS 2 and :program:`colcon` auto-completion scripts,
ensuring they are loaded in every new shell session
(:program:`Workshop` uses :program:`bash` by default).


Configure :program:`colcon` defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 72-98

Creates directories and a default configuration file for :program:`colcon`,
specifying paths for build, install, and log files.

.. important::

   This is where the :samp:`colcon-cache` plug from :file:`sdkcraft.yaml`
   comes into play;
   the configuration points the build actions there instead of the default path.


Add :program:`colcon` mixins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 100-107

Clones the :program:`colcon` mixin repository
and adds default mixins for :program:`colcon`,
updating them as necessary.

Again, the directory configured for the :samp:`colcon-cache` plug is used.


Install :program:`rosdep` dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: design-sdk/setup-base.txt
   :language: shell
   :lines: 109-120

Initialises :program:`rosdep`,
a tool for installing system dependencies,
updates it for our ROS 2 distribution,
then installs dependencies for the project located under :file:`/project/`,
if any.

.. important::

   This means that the intended way of using this SDK
   is to put the ROS 2 sources in the *project directory* of the workshop
   *before* actually launching or refreshing the workshop;
   the sources will be mapped from the host to the :file:`/project/` directory,
   so this part of the hook will find and install the dependencies for the user.


Run-time behaviour
------------------

At run-time, SDK revisions are available inside the workshop;
under :file:`/var/lib/workshop/sdk/ros2/`,
you can see all SDK content that was packed, published and installed.
There, :file:`current/` always maps to the latest installed revision:

.. code-block:: console

   $ workshop shell ros2-jazzy
   workshop@ros2-jazzy-8584e57d$ ls /var/lib/workshop/sdk/ros2/current

   meta  sdk


The :file:`meta/` directory contains the definition,
whereas :file:`sdk/` stores hooks (and will store any other content
when respective features are eventually added).


Summary
-------




See also
--------

Explanation:

- :ref:`exp_sdk_definition`
- :ref:`exp_sdk_hooks`
- :ref:`exp_sdk_interfaces`
- :ref:`exp_sdk_parts`

Reference:

- :ref:`ref_content_interface`
- :ref:`ref_gpu_interface`
- :ref:`ref_sdk_definition`
- :ref:`ref_sdk_hooks`
- :ref:`ref_sdk_parts`
