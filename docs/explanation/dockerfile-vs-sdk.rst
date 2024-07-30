.. _exp_dockerfile_vs_sdk:

How a Dockerfile compares to an SDK
===================================

:program:`Workshop` didn't happen in a vacuum; there have been many attempts
to provide developers with robust environments.
A common approach is to use :program:`Docker`
to achieve repeatability, persistence, layering, and various other benefits
that the technology offers.

We won't dwell on the pros and cons here;
instead, let's discuss how a typical Dockerfile development environment
maps to a workshop and its SDKs.

.. note::

   This discussion assumes you are already familiar
   with the |project_markup| basics covered in the :ref:`tutorial <tutorial>`
   and have a basic understanding of Dockerfiles.


Feature discussion
------------------

To begin with, it's perfectly reasonable to draw a few comparisons
between :program:`Docker` and :program:`Workshop`.


:spellexception:`(Im)mutability`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first contrast comes from the overall approach:
:program:`Docker` images are conceived to be immutable,
whereas workshops are designed to evolve over time.
This affects all aspects of their design and implementation,
including Dockerfiles and SDKs respectively.


Bind mounts
~~~~~~~~~~~

:program:`Docker` provides several ways to manage data persistence and storage
such as the :option:`!--mount` run-time option or :samp:`VOLUME` instructions.
It's important to note that the run-time mount settings
are usually provided by the users themselves;
image authors often prefer to keep their images mount-agnostic,
in line with the aforementioned preference for immutability.

:program:`Workshop` reciprocates this functionality
with the :ref:`content interface <exp_content_interface>`
and the :command:`workshop remount` command,
but the key difference is
that the person responsible for implementing the actual mount logic
is the domain-savvy author of the SDK,
not the user;
unless the user absolutely needs to intervene,
the workings of the mounts defined in the SDKs by their publishers
are transparent to the workshop.


Resource usage
~~~~~~~~~~~~~~

For largely historical reasons,
:program:`Docker`'s way of accessing various host resources
can be remarkably disparate;
for example, enabling GPU pass-through is entirely different to SSH forwarding.

In contrast, :program:`Workshop` aims to unify these mechanisms
under the single concept of an :ref:`interface <exp_sdk_interfaces>`,
providing a consistent way to uniformly manage host resource access.


Parts and layers
~~~~~~~~~~~~~~~~

:program:`Docker` relies on temporally layered approach,
where each change is built on top of the previous one.

Our SDKs are structured using :ref:`parts <exp_sdk_parts>`;
their expressiveness are more diverse and semantically rich,
allowing the layout of an SDK to be formalised in a modular way.
If necessary, the layered approach
can be mimicked using :ref:`SDK hooks <exp_sdk_hooks>`,
although :program:`Workshop` doesn't yet support layering.


Build commands
~~~~~~~~~~~~~~

In :program:`Docker`,
build commands are typically bundled as :samp:`RUN` instructions.

In our SDKs,
the :samp:`setup-base` :ref:`hook <exp_sdk_hooks>` is responsible for building the workshop,
but other hooks add extra functionality with run-time events and health checks.


Feature mapping
---------------

It's obvious now that any attempt at one-to-one mapping
between these different, albeit vaguely similar, technologies is futile.
Again, a key difference is that a Dockerfile is controlled by the user,
whereas a workshop is managed by the user but relies on publisher-defined SDKs
whose definitions are beyond the user's reach.

This means that some aspects of implementation
accessible to the :program:`Docker` user
won't be available to a user of :program:`Workshop`,
so the design process is split between the user-oriented :program:`Workshop`
and the publisher-focused |project_markup|.

However, we can still argue that certain Dockerfile features
can be implemented in :program:`Workshop`
using the capabilities offered by both the workshop itself and its SDKs.
Various Dockerfile instructions can be approximated
with :program:`Workshop` and |project_markup| as follows:

.. list-table::
   :header-rows: 1
   :widths: 2 5 4

   * - Dockerfile
     - :program:`Workshop`
     - |project_markup|

   * - :samp:`ADD`
     -  
     - :ref:`parts <exp_sdk_parts>`, :ref:`content interface <exp_content_interface>`

   * - :samp:`CMD`
     - :command:`workshop exec`, :command:`workshop shell`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`COPY`
     -  
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`ENTRYPOINT`
     - :command:`workshop exec`, :command:`workshop shell`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`ENV`
     - :command:`workshop exec` with :option:`!--env` set
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`FROM`
     - :samp:`base` in the workshop definition
     - :samp:`base` in the :ref:`SDK definition <exp_sdk_definition>`

   * - :samp:`HEALTHCHECK`
     -  
     - :samp:`check-health` hook

   * - :samp:`ONBUILD`
     -  
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`RUN`
     - :command:`workshop exec`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`SHELL`
     - :command:`workshop shell`
     -  

   * - :samp:`USER`
     - :command:`workshop exec` with :option:`!--uid` and :option:`!--gid` set
     -  

   * - :samp:`VOLUME`
     - :command:`workshop remount`
     - :ref:`content interface <exp_content_interface>`

   * - :samp:`WORKDIR`
     - :command:`workshop exec` with :option:`!-w` or :option:`!--cwd` set
     -  


Case study: ROS 2
-----------------

For a specific example,
consider the official developer Dockerfile_ for ROS 2,
the open-source robotics operating system.
The choice is influenced by many factors,
notably because we have a ROS 2 SDK available for comparison;
for details, refer to the corresponding how-to guide
in the `See also`_ section.

Nonetheless, we won't focus on the specifics of ROS 2 here;
instead, we will discuss how certain parts of an arbitrary elaborate Dockerfile
map to a similar SDK and the workshop that uses it.


Base image
~~~~~~~~~~

The Dockerfile says:

.. code-block:: docker

   FROM ubuntu:noble-20240605

In :program:`Workshop`'s terms, this translates to :samp:`ubuntu@24.04`
in the :ref:`SDK definition <exp_sdk_definition>`;
the same base should appear in the definition of the workshop itself.


Working directory
~~~~~~~~~~~~~~~~~

Next, let's look at how the approach to the working directory differs.

The Dockerfile establishes it as follows:

.. code-block:: docker

   # clone source
   ENV ROS2_WS /opt/ros2_ws
   RUN mkdir -p $ROS2_WS/src
   WORKDIR $ROS2_WS


But the SDK is more elaborate.
First, it builds a hierarchy in the default home directory:

.. code-block:: shell

   _WORKSHOP_USER="workshop"
   _WORKSHOP_USER_HOME="/home/${_WORKSHOP_USER}"
   _WORKSHOP_COLCON_BASE_PATH="${_WORKSHOP_USER_HOME}/colcon"
   _WORKSHOP_COLCON_CONFIG_BASE_PATH="${_WORKSHOP_USER_HOME}/.colcon"


But distinguishes it from the project directory:

.. code-block:: shell

   _WORKSHOP_PROJECT_BASE_PATH="/project"


Remember that the host directory where the workshop was defined and launched
is mapped to the *project* directory, not the home directory.

Next, the hook modifies the default :samp:`.bashrc`,
then creates and populates :program:`colcon`'s directories in the hierarchy,
effectively establishing a foundation for the workshop's run-time behaviour;
the build artefacts of ROS 2 are eventually stored in the *project* directory.


Build commands
~~~~~~~~~~~~~~

Normally, everything under a :samp:`RUN` instruction in a Dockerfile
translates to the :samp:`setup-base` :ref:`hook <exp_sdk_hooks>` in an SDK
pretty much unchanged.
Here, the steps to
`set up keys <https://github.com/osrf/docker_images/blob/248dd4b04e98ff136921f3a4f328d42c0dbc927c/ros2/source/devel/Dockerfile#L35>`_,
then `configure the repositories <https://github.com/osrf/docker_images/blob/248dd4b04e98ff136921f3a4f328d42c0dbc927c/ros2/source/devel/Dockerfile#L45>`_
and `install the packages <https://github.com/osrf/docker_images/blob/248dd4b04e98ff136921f3a4f328d42c0dbc927c/ros2/source/devel/Dockerfile#L52>`_
would largely stay the same.

However, :samp:`setup-base` runs with the project directory already mounted,
which means that some :samp:`ONBUILD` features
can be implemented with the same hook.
Here, this enables the ROS 2 SDK
to identify and install project-specific dependencies,
eliminating the need to do this manually
as would be the case with the Dockerfile.

For instance, this Dockerfile instruction:

.. code-block:: docker

   # bootstrap rosdep
   RUN rosdep init \
       && rosdep update
   
   # setup colcon mixin and metadata
   RUN colcon mixin add default ... && \
       colcon mixin update && \
       colcon metadata add default ... && \
       colcon metadata update


Largely corresponds to this section of :samp:`setup-base` from the ROS 2 SDK
(note the use of the variables from the previous section):

.. code-block:: shell

   # Add colcon's default mixins
   if [ ! -d "${_WORKSHOP_COLCON_CONFIG_BASE_PATH}/colcon-mixin-repository" ] ; then
     sudo -u ${_WORKSHOP_USER} bash -c "git -C ${_WORKSHOP_COLCON_CONFIG_BASE_PATH} clone https://github.com/colcon/colcon-mixin-repository.git"
   fi
   if [! -f ${_WORKSHOP_COLCON_CONFIG_BASE_PATH}/mixin_repositories.yaml ] || ! grep -q "default:" "${_WORKSHOP_COLCON_CONFIG_BASE_PATH}/mixin_repositories.yaml"; then
     sudo -u ${_WORKSHOP_USER} bash -c "colcon mixin add default file://${_WORKSHOP_COLCON_CONFIG_BASE_PATH}/colcon-mixin-repository/index.yaml"
   fi
   sudo -u ${_WORKSHOP_USER} bash -c "colcon mixin update default"

   # Initialise rosdep
   if [ ! -f "/etc/ros/rosdep/sources.list.d/20-default.list" ]; then
     rosdep init
   fi
   sudo -H -E -u ${_WORKSHOP_USER} bash -c "rosdep update --rosdistro=${_WORKSHOP_ROS_DISTRO}"


Lastly, the SDK adds steps that implement project-specific logic
on top of the defaults:

.. code-block:: shell

   # Install project's dependencies
   if [ -d "${_WORKSHOP_PROJECT_BASE_PATH}" ]; then
     if [ ! -z "$(ls -A ${_WORKSHOP_PROJECT_BASE_PATH})" ]; then
       sudo -H -i -u ${_WORKSHOP_USER} bash -c "rosdep install --default-yes --ignore-packages-from-source --rosdistro=${_WORKSHOP_ROS_DISTRO} --from-paths ${_WORKSHOP_PROJECT_BASE_PATH}/."
     fi
   fi


See also
--------

How-to guides:

- :ref:`how_create_ros2_sdk`

Reference:

- :ref:`ref_sdk_definition`
- :ref:`ref_sdk_hooks`


.. LINKS
.. wokeignore:rule=master
.. _Dockerfile: https://github.com/osrf/docker_images/blob/master/ros2/source/devel/Dockerfile
