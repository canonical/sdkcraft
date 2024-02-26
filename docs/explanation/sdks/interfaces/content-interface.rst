.. _exp_content_interface:

SDK content interface
=====================

The content interface
exposes host file system locations
to individual SDKs
by mounting them inside the workshop
that references these SDKs.


.. _exp_content_plug:

Content interface plug
----------------------

An essential element here is the content interface plug
that is declared in the SDK definition.

A basic structure includes the name of the plug itself,
the interface (:samp:`content`)
and the intended target path inside the workshop:

.. code-block:: yaml
   :caption: sdkcraft.yaml

   name: go
   title: Go SDK
   base: ubuntu@20.04
   summary: The Go programming language
   description: |
     Go is an open source programming language that enables the production
     of simple, efficient and reliable software at scale.

   plugs:
     mod-cache:
       interface: content
       target: /home/workshop/go/pkg/mod


This definition creates a plug called :samp:`mod-cache`
that does the following:

- Sets its :samp:`interface` type to :samp:`content`,
  which makes it a content interface plug

- Points the :samp:`target` directory *inside the workshop*
  to :file:`/home/workshop/go/pkg/mod/`;
  it will be mounted to a file directory on the host system
  that `Workshop`_ designates at run-time


Overall, the intent of this declaration is
to use a directory
(which :program:`Workshop` automatically allocates for the slot)
for persisting the
`module cache <https://go.dev/ref/mod#module-cache>`__
in the host file system
when the workshop stops.


.. _exp_content_slot:

Content interface slot
----------------------

To let SDKs in a workshop access the host file system,
:program:`Workshop` creates a content interface slot,
which multiple content interface plugs can then access.

When the SDK is installed during launch and refresh operations at run-time,
for each plug that targets the slot, :program:`Workshop` checks the following:

- The plug can be installed.

- The plug can be auto-connected
  (for :samp:`content`, it's a yes).

- The :samp:`target` directory already exists in the workshop.

If the plug passes the checks,
it is connected
and a :program:`Workshop`-created directory from the host file system
is mounted to the :samp:`target` directory inside the workshop.
That's where the module cache from our example will end up;
the best part is that it will be preserved
between :program:`Workshop` operations such as
:command:`refresh`, :command:`start` and :command:`stop`,
so you can benefit from a pre-populated module cache without doing extra work.


See also
--------

Explanation:

- :ref:`exp_sdk_definition`
- :ref:`exp_sdk_interfaces`
