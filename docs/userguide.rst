.. _user:

Introduction
============

Wextracto is a tool for extraction of information from web pages.

It works as Unix command line tool sending output to standard output.

Kicking the Tyres
~~~~~~~~~~~~~~~~~

Create yourself a virtual environment.

The `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/>`_ package makes that easy:

.. code-block:: console

    $ mktmpenv

Install Wextracto into that virtual environment:

.. code-block:: console

    $ pip install https://github.corp.ebay.com/gsbrown/wextracto/archive/master.zip


Write a python setup script:

.. literalinclude:: samples/jsonecho/setup.py

Write an extractor function in Python:

.. literalinclude:: samples/jsonecho/jsonecho.py

Set-up for development:

.. code-block:: console

    $ python setup.py develop


And try it out:

.. code-block:: console

    $ wex "http://httpbin.org/user-agent"
    INFO  [requests.packages.urllib3.connectionpool] Starting new HTTP connection (1): httpbin.org
    {"user-agent":"python-requests/2.3.0 CPython/2.7.5 Darwin/13.4.0"}
