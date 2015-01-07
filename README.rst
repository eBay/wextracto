Wextracto: Web Data Extraction
==============================

.. image:: https://travis-ci.org/gilessbrown/wextracto.svg
    :target: http://travis-ci.org/gilessbrown/wextracto
    :alt: Build Status

Wextracto is a toolkit for command-line web data extraction.


Installation
~~~~~~~~~~~~

.. code-block:: bash

    $ pip install wextracto


Kicking the Tyres
~~~~~~~~~~~~~~~~~

.. code-block:: shell

    $ echo -e "[wex]\nsitemaps=wex.sitemaps:urls_from_sitemaps" > entry_points.txt
    $ wex "http://www.ebay.com/robots.txt"


Documentation
~~~~~~~~~~~~~

The documentation can be found here:

    http://wextracto.readthedocs.org/en/latest/index.html
