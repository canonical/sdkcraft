How to contribute
=================

We believe everyone has something valuable to contribute,
whether you're a coder, a writer or a tester.
Here's how and why you could get involved:

- **Why join us**:
  Work with like-minded people, grow your skills,
  connect with diverse professionals and make a difference.

- **What do you get**:
  Personal growth, recognition for your contributions,
  early access to new features and the joy of seeing your work appreciated.

- **Start early, start simple**:
  Dive into code contributions,
  improve documentation or be among the first testers.
  Your presence matters, regardless of experience or the scale of your input.

The guidelines below will keep your contributions effective and meaningful.


Environment setup
-----------------

#. Install the necessary Python packages:

   .. code-block:: console

      sudo apt-get install -y gpg gpgv libpython3-stdlib python3-pip \
        python3-setuptools python3-wheel python3-venv python3-minimal \
        python3-pkg-resources python3-apt python3-pip-whl


#. `Snapcraft <https://snapcraft.io/docs/snapcraft>`_
   is used to build, package and publish ``sdkcraft`` snaps.
   All these processes run in a self-launched
   `LXD <https://documentation.ubuntu.com/lxd/en/latest/>`_ container.
   Install ``snapcraft`` and ``lxd`` using ``snap``:

   .. code-block:: console

      sudo snap install snapcraft --classic
      sudo snap install lxd


   Add the current user to the ``lxd`` group
   to give permission to access its resources:

   .. code-block:: console

      sudo usermod -a -G lxd $USER


   Log out and re-open your user session for the new group to become active,
   then initialise LXD:

   .. code-block:: console

      lxd init --minimal


#. ``Spread`` is the end-to-end testing tool for ``sdkcraft``.
   Install it from `our custom fork <https://github.com/dmitry-lyfar/spread>`_:

   .. code-block:: console

      git clone https://github.com/dmitry-lyfar/spread
      cd spread
      go install ./...


   Make sure the ``$GOPATH/bin`` directory is included in ``$PATH``.
   After successful installation, you should see the help message by running:

   .. code-block:: console

      spread -h


#. A Python virtual environment is recommended
   to make the project easier to maintain:

   .. code-block:: console

      # Create a virtual environment in the current directory
      python -m venv venv --system-site-packages

      # Activate the virtual environment
      source venv/bin/activate


   Make sure to use the ``--system-site-packages`` option,
   as some dependencies can only be accessed as system site packages,
   not virtual environment packages.


#. Install all Python dependency packages:

   .. code-block:: console

      pip install -r requirements-dev.txt


Read the code
-------------

Starting on a new project can be challenging.
Here, begin with this snippet in ``snapcraft.yaml``:

.. code-block:: yaml

   apps:
     sdkcraft:
       command: bin/python -m sdkcraft


That's where the ``sdkcraft`` command starts its logic.
By following the ``sdkcraft/__main__.py`` file,
you can gradually trace how the code is executed step by step.

It's worth mentioning that ``sdkcraft`` is built on top of the `craft-parts
<https://github.com/canonical/craft-parts>`_ project.

Using a Python virtual environment makes it convenient
to add logging code in dependency package files,
so you can gradually unwrap the execution logic.


Coding
------

In SDKcraft, commit messages differ from conventional commits in capitalisation:

.. code-block:: none

   Ensure correct permissions and ownership for the content mounts

    * Work around an LXD issue regarding empty dirs:
      https://github.com/canonical/lxd/issues/12648

    * Ensure the source directory is owned by the user running a workshop.

   Links:
   - ...
   - ...


The messages rarely, if ever, state the type of the commit
(e.g. ``fix``, ``feat``, etc.);
these are used for branch naming, for example:

- ``canonical/feat/workspace-start``
- ``canonical/fix/spread-tests-github``
- ``canonical/chore/update-lxd``


Commits that focus on docs must use the ``Doc:`` type prefix
with an optional scope in square brackets:

.. code-block:: none

   Doc[chore]: Align references


PR descriptions should follow the PR template checklist,
which largely reiterates this section.


Reversibility
~~~~~~~~~~~~~

When making decisions that might be costly to reverse,
explicitly state the rationale in the PR description.
This helps to understand the reasoning and collaborate better.


Coding Standards
~~~~~~~~~~~~~~~~

- **Avoid nested conditions**:
  Refrain from nesting conditions to enhance readability and maintainability.

- **Eliminate dead code and redundant comments**:
  Remove unused or obsolete code and comments.
  This promotes a cleaner code base and reduces confusion.

- **Normalise symmetries**:
  Handle identical operations consistently, using a uniform approach.
  This also improves consistency and readability.


Code structure
~~~~~~~~~~~~~~

- **Check coupled code elements**:
  Verify that coupled code elements, files and directories are adjacent.
  For instance, store test data close to the corresponding test code.

- **Group variable declaration and initialisation**:
  Declare and initialise variables together
  to improve code organisation and readability.

- **Divide large expressions**:
  Break down large expressions
  into smaller self-explanatory parts.
  Use multiple variables if necessary
  to make the code more understandable
  and choose names to reflect their purpose.

- **Use blank lines for logical separation**:
  Insert a blank line between two logically distinct sections of code.
  This improves its structure and makes it easier to comprehend.


Testing
-------

Make sure to run unit and integration tests before submitting a PR.

Run unit tests:

.. code-block:: console

   make test-units


Run integration tests (should run on Ubuntu 22.04):

.. code-block:: console

   make test-integrations

Run end-to-end tests:

.. code-block:: console

   make spread


Documentation
-------------

All documentation resides in the ``docs/`` directory.
To build and run it at ``127.0.0.1:8000``:

.. code-block:: console

   make run


To suggest changes online, use the GitHub link in the footer of the page
or submit a PR, limiting it to the ``docs/`` directory
and following our internal `Sphinx and Read the Docs guide
<https://canonical-documentation-with-sphinx-and-readthedocscom.readthedocs-hosted.com/>`_.
