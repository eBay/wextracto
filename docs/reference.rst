.. _reference:

Reference
=========

The Wextracto reference.

.. #wextract/cache.py
   #wextract/ftp.py
   #wextract/http.py
   #wextract/iterable.py
   #wextract/lxml.py
   #wextract/output.py
   #wextract/pytestplugin.py
   #wextract/readable.py
   #wextract/regex.py
   #wextract/response.py
   #wextract/save.py
   #wextract/url.py

Command
-------

Wextracto exposes one command, ``wex``, as a
`console_script <https://pythonhosted.org/setuptools/setuptools.html#automatic-script-creation>`_.

For information on the options use the --help argument:

.. code-block:: sh

    $ wex --help


Extractor
---------

Extractor functions are registered as `entry points <https://pythonhosted.org/setuptools/setuptools.html#dynamic-discovery-of-services-and-plugins>`_ under the group ``[wex]``.

Extractor functions take a single :class:`wex.response.Response` argument
and yields tuples that are serialized and written to standard output.

A minimal extractor function would looks like this:

.. code-block:: python

    def extractor(response):
        yield ("something",)

Response
--------
.. autoclass:: wex.response.Response


Output
------

.. automodule:: wex.output


Composed Functions
------------------

.. automodule:: wex.composed
