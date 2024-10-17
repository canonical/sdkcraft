:relatedlinks: [Workshop](https://canonical-workshop.readthedocs-hosted.com/), [Craft CLI](https://craft-cli.readthedocs.io/)

.. _home:

|project_markup|
================

.. toctree::
   :hidden:

   Home <self>
   tutorial/index
   how-to/index
   explanation/index
   reference/index
   Contribution <contributing>


**A tool that packages and publishes SDKs
to be used with Workshop,
a related user-facing product**.

**Define your SDK in simple YAML**.
Next, |project_markup| instantiates the definition
and snapshots the resulting SDK into a tarball,
which you can then publish to be retrieved and used with :program:`Workshop`.

**Describe your project's ins and outs in a consistent manner**.
Use a common, instantly recognisable paradigm
to make all aspects of your setup and usage explicit.
|project_markup| provides a uniform way to bake in your domain expertise
instead of leaving the users to figure everything out by trial and error.

**For those who maintain and distribute complex SDKs and frameworks**.
Many software domains have less-than-trivial project layouts
that require significant effort to set up and support.
That’s where |project_markup| gives you an edge
by making your product easier to package, distribute, install and use.

---------


In this documentation
---------------------

.. grid:: 1 1 2 2

   .. grid-item:: :doc:`Tutorial <tutorial/index>`

      **Starter instructions** for new users of |project_markup|


   .. grid-item:: :doc:`Explanation <explanation/index>`

      **Discussion and clarification** of key topics


   .. grid-item:: :doc:`How-to guides <how-to/index>`

      **Step-by-step guides** covering common tasks

   .. grid-item:: :doc:`Reference <reference/index>`

      **Technical details**, specifications, APIs

---------


Project and community
---------------------

|project_markup| is an emergent project
within the Enterprise Engineering department here at Canonical;
`Workshop <https://canonical-workshop.readthedocs-hosted.com/>`_
is its older sibling,
aimed at users who consume SDKs built with |project_markup|.

At their core, both projects build upon Canonical's mature tech.
They use `LXD <https://documentation.ubuntu.com/lxd/>`_
as the underlying container technology;
they also follow the tooling paradigm exemplified by
`Snap <https://snapcraft.io/docs/>`_
and implemented with
`Craft CLI <https://craft-cli.readthedocs.io/>`_.

Talk to us if you have a project
you’d like to try with |project_markup| and :program:`Workshop`:
we'll help you get it out there.
Tell us about the frustrating parts of your experience,
and we'll see what we can do.


- `Code of conduct <https://ubuntu.com/community/ethos/code-of-conduct>`__

- `Pulse reviews on Discourse <https://discourse.canonical.com/c/engineering/sdk/34>`__

- `Mattermost channel <https://chat.canonical.com/canonical/channels/sdk>`__

- `Product map <https://warthogs.atlassian.net/jira/software/c/projects/WSP/boards/1645>`__

- :doc:`Contribution and participation <contributing>`

- `Product and documentation feedback <https://github.com/canonical/sdkcraft/issues>`__
