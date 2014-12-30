Wextracto: Web Data Extraction
==============================

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
