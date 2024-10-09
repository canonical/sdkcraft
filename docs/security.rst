Security
========

This is an overview of security aspects and considerations for ``SDKcraft``.


Privileges
----------

``SDKcraft`` is an instance of `craft-application
<https://github.com/canonical/craft-application/>`_,
built, installed and run as a snap;
it neither needs nor requires elevated privileges to work
and securely confines the SDK build process to a container.

Packaged SDKs are uploaded to the SDK Store.
Currently, it's implemented using `GCP
<https://console.cloud.google.com/storage/browser/sdk-store>`_,
so access is managed by `GCP IAM
<https://cloud.google.com/security/products/iam>`_.


Isolation
---------

By design, all SDKs in a workshop can access any data inside it,
but have limited capabilities on the host.
To achieve this, LXD is used to add a level of confinement:
everything ``Workshop`` users do ends up in a `non-privileged container
<https://documentation.ubuntu.com/server/how-to/containers/lxd-containers/#uid-mappings-and-privileged-containers>`_
within a dedicated `project <https://documentation.ubuntu.com/lxd/en/latest/explanation/projects/>`_,
which separates workshops that belong to different users
and isolates them from each other and the host system.


Interfaces
----------

In ``SDKcraft``, the interface mechanism plays a role in maintaining security
by controlling access between the SDKs and the host system;
the implementation is largely similar to ``snapd``'s
`interface manager <https://snapcraft.io/docs/interface-management>`__:

- Interfaces define and control what resources an SDK can use,
  ensuring that permissions are explicitly granted and limited in scope.

- They are used to explicitly provide access to resources
  such as files, the GPU or the SSH agent.

- SDKs in a workshop, or the workshop itself,
  must declare the interfaces and the connections they need.
  This limits the resources an SDK can access.

- Some interfaces, such as mounts, are connected automatically by default;
  others require manual approval by the user.
  All connections are subject to ``Workshop``'s built-in validation policies.

- The use of interfaces reflects the least privilege principle,
  allowing publishers and users to request only the necessary permissions,
  reducing the attack surface.


Risks
-----

Although safeguards are in place,
the security of an SDK largely depends on how it's designed.
For instance, it is advisable not to store sensitive data within workshops.
Instead, use mounts to provide access to sensitive data if your SDKs need it.


Supported versions
------------------

It is best to use the latest release from GitHub;
older releases may have known bugs
or be incompatible with latest changes.


Reporting a vulnerability
-------------------------

As with other high-priority issues,
report concerns in our
`Mattermost channel <https://chat.canonical.com/canonical/channels/sdk>`__
or `GitHub issues <https://github.com/canonical/sdkcraft/issues>`__.
