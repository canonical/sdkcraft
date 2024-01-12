# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= -c . -d .sphinx/.doctrees
SPHINXBUILD   ?= sphinx-build
SPHINXDIR     = .sphinx
SOURCEDIR     = .
BUILDDIR      = _build
VENVDIR       = $(SPHINXDIR)/venv
PA11Y         = $(SPHINXDIR)/node_modules/pa11y/bin/pa11y.js
VENV          = $(VENVDIR)/bin/activate


# Put it first so that "make" without argument is like "make help".
.PHONY: help
help: install
	. $(VENV); $(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" \
        $(SPHINXOPTS) $(O)


# Explicit target avoids fall-through to the "Makefile" target.
$(SPHINXDIR)/requirements.txt:
	test -f $(SPHINXDIR)/requirements.txt


# If requirements are updated, venv should be rebuilt and timestamped.
$(VENVDIR): $(SPHINXDIR)/requirements.txt
	@echo "... setting up virtualenv"
	python3 -m venv $(VENVDIR)
	. $(VENV); pip install --require-virtualenv \
	    --upgrade -r $(SPHINXDIR)/requirements.txt \
            --log $(VENVDIR)/pip_install.log
	@test ! -f $(VENVDIR)/pip_list.txt || \
            mv $(VENVDIR)/pip_list.txt $(VENVDIR)/pip_list.txt.bak
	@. $(VENV); pip list --local --format=freeze > $(VENVDIR)/pip_list.txt
	@echo "\n" \
	        "--------------------------------------------------------------- \n" \
        "* watch, build and serve the documentation: make run \n" \
        "* only build: make html \n" \
        "* only serve: make serve \n" \
        "* clean built doc files: make clean-doc \n" \
        "* clean full environment: make clean \n" \
        "* check links: make linkcheck \n" \
        "* check spelling: make spelling \n" \
        "* check inclusive language: make woke \n" \
		"* check accessibility: make pa11y \n" \
        "* other possible targets: make <press TAB twice> \n" \
        "--------------------------------------------------------------- \n"
	@touch $(VENVDIR)


.PHONY:  woke-install
woke-install:
	@type woke >/dev/null 2>&1 || \
		{ echo "Installing \"woke\" snap... \n"; sudo snap install woke; }

.PHONY:  pa11y-install
pa11y-install:
	@type $(PA11Y) >/dev/null 2>&1 || { \
			echo "Installing \"pa11y\" from npm... \n"; \
			mkdir -p $(SPHINXDIR)/node_modules/ ; \
			npm install --prefix $(SPHINXDIR) pa11y; \
		}


.PHONY:  install
install: $(VENVDIR) woke-install pa11y-install


.PHONY: run
run: install
	. $(VENV); sphinx-autobuild -b dirhtml "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)


# Doesn't depend on $(BUILDDIR) to rebuild properly at every run.
.PHONY: html
html: install
	. $(VENV); $(SPHINXBUILD) -b dirhtml "$(SOURCEDIR)" "$(BUILDDIR)" \
		-w .sphinx/warnings.txt $(SPHINXOPTS)


.PHONY: epub
epub: install
	. $(VENV); $(SPHINXBUILD) -b epub "$(SOURCEDIR)" "$(BUILDDIR)" \
		-w .sphinx/warnings.txt $(SPHINXOPTS)


.PHONY: serve
serve: html
	cd "$(BUILDDIR)"; python3 -m http.server 8000


.PHONY: clean
clean: clean-doc
	@test ! -e "$(VENVDIR)" -o -d "$(VENVDIR)" -a \
		"$(abspath $(VENVDIR))" != "$(VENVDIR)"
	rm -rf $(VENVDIR)
	rm -rf .sphinx/.doctrees
	rm -rf .sphinx/node_modules

.PHONY: clean-doc
clean-doc:
	git clean -fx "$(BUILDDIR)"


.PHONY: spelling
spelling: html
	. $(VENV) ; python3 -m pyspelling -c .sphinx/spellingcheck.yaml


.PHONY: linkcheck
linkcheck: install
	. $(VENV) ; $(SPHINXBUILD) -c . -b linkcheck  "$(SOURCEDIR)" "$(BUILDDIR)"


.PHONY: woke
woke:
	woke *.rst **/*.rst --exit-1-on-failure \
	    -c https://github.com/canonical/Inclusive-naming/raw/main/config.yml

.PHONY: pa11y
pa11y: html
	find $(BUILDDIR) -name *.html -print0 | xargs -n 1 -0 $(PA11Y)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
.PHONY: Makefile
%: Makefile
	. $(VENV); $(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
