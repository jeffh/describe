# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) docs

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  test       to run tests the code base"
	@echo "  pypi       to upload the code to pypi"
	@echo "  docs       to generate docs (html, man)"
	@echo "  html       to make HTML doc files named index.html in directories"
	@echo "  man        to make manual pages"
	@echo "  check_docs to check all external links for integrity"

clean:
	-rm -rf $(BUILDDIR)/* dist
	find . -iname "*.pyc" | xargs rm

docs: check_docs html man

test:
	python setup.py test
	
pypi: test docs
	python setup.py build register upload
	rm -rf describe.egg-info

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

man:
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) $(BUILDDIR)/man
	@echo
	@echo "Build finished. The manual pages are in $(BUILDDIR)/man."

check_docs:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."
