How to contribute
=================

We believe everyone has something valuable to contribute,
whether you're a coder, a writer or a tester.
Here's how and why of your potential involvement:

- **Why join us?** Work with fellow-minded people, grow your skills,
  connect with diverse professionals, and make a difference.

- **What do you get?** Personal growth, recognition for your contributions,
  early access to new features and the joy of seeing your work appreciated.

- **Start early, start simple**: Dive into code contributions,
  improve documentation, or be among the first testers.
  Your presence matters regardless of experience or the scale of your input.

The guidelines below will keep your contributions effective and meaningful.


Environment Setup
--------------------------------------------


Install necessary python packages:

.. code-block:: console

  sudo apt-get install -y gpg gpgv libpython3-stdlib python3-pip python3-setuptools python3-wheel python3-venv python3-minimal python3-pkg-resources python3-apt python3-pip-whl


``snapcraft`` is the tool to build, package and publish ``sdkcraft`` snap.
All these processes run in a self-launched LXD container.
Install ``snapcraft`` and ``lxd`` by snap:

.. code-block:: console

  sudo snap install snapcraft --classic
  sudo snap install lxd

  # Add current user to the lxd group to give yourself permission to access its resources:
  sudo usermod -a -G lxd $USER

  # Logout and re-open your user session for the new group to become active.

  # Initialize LXD:
  lxd init --minimal


``spread`` is the end-to-end testing tool for sdkcraft. Install spread from
the `fork <https://github.com/dmitry-lyfar/spread>`_:

.. code-block:: console

  git clone https://github.com/dmitry-lyfar/spread
  cd spread
  go install ./...

  # make sure $GOPATH/bin directory is included in $PATH
  # after successful installation, you should see help message by:
  spread -h


Python virtual environment makes the project easy to troubleshot and maintain.
It's not required but recommended.

.. code-block:: console

  # Create a virtual env in current dir
  python -m venv venv --system-site-packages

  # Activate virtual env
  source venv/bin/active


Note: you have to enable ``--system-site-packages``
option for python virtual env.
As some dependencies can only be accessed as system site package, not virtual env package.


Install all python dependency packages:

.. code-block:: console

  pip install -r requirements-dev.txt


Read the Code
--------------------------------------------

Starting on a new project can always be challenging. However,
you can begin by looking at this snippet in ``snapcraft.yaml`` file:

.. code-block:: yaml

  apps:
    sdkcraft:
      command: bin/python -m sdkcraft

That's where the ``sdkcraft`` command starts its logic.
By following the ``sdkcraft/__main__.py`` file, you can gradually trace how the code is executed step by step.


``sdkcraft`` is built on top of `craft_parts <https://github.com/canonical/craft-parts>`_.


Using a python virtual environment make it convenient to add
logging code in dependency package files.
So you can understand the execution logic easier.



Coding
------

Sdkcraft's commit messages differ from conventional commits in capitalisation:

.. code-block:: none

   Ensure correct permissions and ownership for the content mounts
    
    * Work around an LXD issue regarding empty dirs:
      https://github.com/canonical/lxd/issues/12648
    
    * Ensure the source directory is owned by the user running a workshop.

   Links:
   - ...
   - ...

The messages rarely if ever state the type of the commit,
e.g. ``fix``, ``feat``, etc.;
these are used for branch naming, for example:

- ``canonical/feat/workspace-start``
- ``canonical/fix/spread-tests-github``
- ``canonical/chore/update-lxd``


However, documentation-related commits use the ``Doc:`` type prefix
with an optional scope in square brackets:

.. code-block:: none

   Doc[chore]: Align references


PR descriptions should follow the PR template checklist
that largely reiterates this section.


Reversibility
~~~~~~~~~~~~~

When making decisions that might be costly to reverse,
explicitly state the rationale in the PR description.
This helps to understand the reasoning and collaborate better.


Coding standards
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
  Verify that coupled code elements, files, and directories are adjacent.
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
--------------------------------------------

.. code-block:: console

  # Run unit tests
  make test-units

  # Run integration tests - should run on ubuntu-22.04
  make test-integrations

  # Run end-to-end tests
  make spread


Documentation
-------------

All documentation resides in the ``docs/`` directory.
To build and run it at ``127.0.0.1:8000``:

.. code-block:: console

   make run


To suggest changes online, use the GitHub link in the footer of the page
or submit a PR, limiting it to the ``docs/`` directory
and following our internal
`Sphinx and Read the Docs guide
<https://canonical-documentation-with-sphinx-and-readthedocscom.readthedocs-hosted.com/>`_.
