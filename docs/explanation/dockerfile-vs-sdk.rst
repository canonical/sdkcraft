.. _exp_dockerfile_vs_sdk:

How a Dockerfile compares to an SDK
===================================

:program:`Workshop` and |project_markup| didn't happen in a vacuum;
there have been many attempts to provide developers with robust environments.
A common approach is to use Docker
to achieve repeatability, persistence, layering, and various other benefits
that the technology offers.

We won't dwell on the pros and cons here;
instead, let's discuss how a typical Dockerfile development environment
maps to a workshop and its SDKs.

.. note::

   We assume you're familiar
   with |project_markup| essentials covered in the :ref:`tutorial <tutorial>`
   and have a basic understanding of Docker.


Feature discussion
------------------

To begin with, it's perfectly reasonable to draw a few comparisons
between Docker and :program:`Workshop`.


:spellexception:`(Im)mutability`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first contrast comes from the overall approach:
Docker images are conceived to be immutable,
whereas workshops are designed to evolve over time.
This affects all aspects of their design and implementation,
including how Dockerfiles and, respectively, SDKs are laid out.


Bind mounts
~~~~~~~~~~~

Docker provides several ways to manage data persistence and storage
such as the :option:`!--mount` run-time option or :samp:`VOLUME` instructions.
It's important to note that
the expectations for mount configuration are set by the image author
but the actual parameters are provided by users at the author's guidance;
the resulting manual process is error-prone and adds unnecessary overhead.

:program:`Workshop` internalises and reciprocates this
with the :ref:`content interface <exp_content_interface>`
and the :command:`workshop remount` command,
but the key difference is
that the person responsible for implementing the mount logic
is the domain-savvy author of the SDK,
not the user;
unless the user absolutely needs to intervene,
the workings of the mounts defined in the SDKs by their publishers
are transparent to the workshop.


Resource usage
~~~~~~~~~~~~~~

For largely historical reasons,
the Docker way of accessing various host resources
can be notably inconsistent;
for example, enabling GPU pass-through is visibly different from SSH forwarding.

In contrast, :program:`Workshop` aims to unify these mechanisms
under the single concept of an :ref:`interface <exp_sdk_interfaces>`,
providing a consistent way to uniformly manage host resource access.


Parts and layers
~~~~~~~~~~~~~~~~

Docker relies on temporally layered approach,
where each change is built on top of the previous one.

Our SDKs are structured using :ref:`parts <exp_sdk_parts>`;
their expressiveness makes them more diverse and semantically rich,
allowing the layout of an SDK to be formalised in a modular way.
If necessary, the layered approach
can be mimicked using :ref:`SDK hooks <exp_sdk_hooks>`,
although :program:`Workshop` doesn't yet support layering.


Build commands
~~~~~~~~~~~~~~

In Docker,
build commands are typically bundled as :samp:`RUN` instructions.

In our SDKs,
the :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`
is responsible for building the workshop,
but other hooks add extra functionality with run-time events and health checks.


Feature mapping
---------------

Any attempt at a straightforward comparison of these different,
albeit vaguely similar, technologies is futile.
Again, a key difference is that a Dockerfile is controlled by the user,
but a workshop is *managed* by the user, yet it relies on publisher-defined SDKs
whose layout is beyond the user's reach.

This means that some capabilities of Docker
won't be available to a user of :program:`Workshop` alone,
so the functionality is split between the user-oriented :program:`Workshop`
and the publisher-focused |project_markup|.

Important Dockerfile instructions are mapped to |project_markup| as follows:

.. list-table::
   :header-rows: 1

   * - Dockerfile
     - SDKcraft

   * - :samp:`ADD`
     - :ref:`parts <exp_sdk_parts>`,
       :ref:`content interface <exp_content_interface>`

   * - :samp:`CMD`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`COPY`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`ENTRYPOINT`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`ENV`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`FROM`
     - :samp:`base` in the :ref:`SDK definition <exp_sdk_definition>`

   * - :samp:`HEALTHCHECK`
     - :samp:`check-health` hook

   * - :samp:`ONBUILD`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`RUN`
     - :samp:`setup-base` :ref:`hook <exp_sdk_hooks>`

   * - :samp:`VOLUME`
     - :ref:`content interface <exp_content_interface>`


In turn, Docker subcommands can be mapped to :program:`Workshop` like this:

.. list-table::
   :header-rows: 1

   * - Docker CLI
     - Workshop CLI

   * - :command:`docker build`
     - :command:`workshop launch`

   * - :command:`docker exec`
     - :command:`workshop exec`, :command:`workshop shell`

   * - :command:`docker images`, :command:`docker ps`
     - :command:`workshop info`, :command:`workshop list`

   * - :command:`docker logs`
     - :command:`workshop changes`, :command:`workshop tasks`

   * - :command:`docker rm`, :command:`docker rmi`
     - :command:`workshop remove`

   * - :command:`docker run`
     - :command:`workshop start`

   * - :command:`docker run --mount`, :command:`docker volume`
     - :command:`workshop remount`

   * - :command:`docker stop`
     - :command:`workshop stop`


Case study: ROS 2
-----------------

For a specific example,
consider the
`Docker-based tutorial <https://docs.ros.org/en/jazzy/How-To-Guides/Setup-ROS-2-with-VSCode-and-Docker-Container.html>`__
for ROS 2,
the open-source robotics operating system.
The choice is influenced by many factors,
including the fact that we have a ROS 2 SDK available for comparison;
for details, refer to the corresponding how-to guide under `See also`_.

Nonetheless, we won't focus on the specifics of ROS 2 here;
instead, we discuss how certain parts
of an arbitrarily sophisticated Dockerfile
map to a similar SDK and the workshop that uses it.


Base image
~~~~~~~~~~

The example suggests using the :samp:`ros:rolling` tag for the
`Dockerfile <https://docs.ros.org/en/jazzy/How-To-Guides/Setup-ROS-2-with-VSCode-and-Docker-Container.html#edit-dockerfile>`_;
with a few `levels of indirection <https://hub.docker.com/_/ros/>`_,
it come down to this (or similar) instruction:

.. code-block:: docker

   FROM ubuntu:noble


For :program:`Workshop`, this translates to :samp:`ubuntu@24.04`
in the :ref:`SDK definition <exp_sdk_definition>` and the workshop definition.


Project files
~~~~~~~~~~~~~

The
`project workspace
<https://docs.ros.org/en/jazzy/How-To-Guides/Setup-ROS-2-with-VSCode-and-Docker-Container.html#edit-devcontainer-json-for-your-environment>`_
in the example is configured by the user at run-time:

.. code-block:: json

   "workspaceMount": "source=${localWorkspaceFolder},target=/home/ws/src,type=bind"


For :program:`Workshop`, this is auto-mounted project directory,
where the workshop was defined and launched;
any files there appear under :file:`/project/` inside the workshop.
Also, additional mounts are configured via the
:ref:`content interface <exp_content_interface>`
by the SDK author, not the user, so no manual setup is needed either.

If the user needs to adjust anything,
the :command:`workshop remount` command provides
the required degree of control and security
without the need to redefine the workshop (or the ability to circumvent it).


Build commands
~~~~~~~~~~~~~~

Normally, a :samp:`RUN` instruction in a Dockerfile
translates to the :samp:`setup-base` :ref:`hook <exp_sdk_hooks>` in an SDK
pretty well.
Here, the steps to
`set up keys <https://github.com/osrf/docker_images/blob/7f98ddd88d872299c45b60c8bcd70d4eb6665222/ros/rolling/ubuntu/noble/ros-core/Dockerfile#L19>`_,
then `configure the repos <https://github.com/osrf/docker_images/blob/7f98ddd88d872299c45b60c8bcd70d4eb6665222/ros/rolling/ubuntu/noble/ros-core/Dockerfile#L29>`_
and `install the packages <https://github.com/osrf/docker_images/blob/7f98ddd88d872299c45b60c8bcd70d4eb6665222/ros/rolling/ubuntu/noble/ros-core/Dockerfile#L38>`_
largely stay the same.

However, :samp:`setup-base` runs with the project directory already mounted,
so any steps that rely on the contents of the project itself
can be implemented with the same hook.
In particular, this enables the ROS 2 SDK
to transparently identify and install project-specific dependencies.


See also
--------

How-to guides:

- :ref:`how_create_ros2_sdk`

Reference:

- :ref:`ref_sdk_definition`
- :ref:`ref_sdk_hooks`
