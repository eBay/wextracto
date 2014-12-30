.. _userguide:

##########
User Guide
##########

What is Wextracto?
~~~~~~~~~~~~~~~~~~

Wextracto is a `Python <https://www.python.org/>`_ package designed to be the
core of a 
`web crawling/scraping <http://en.wikipedia.org/wiki/Web_crawler>`_ system.

Why Just the Core?
~~~~~~~~~~~~~~~~~~

To answer this question, let us look at the general architecture of a web 
crawling/scraping based on Wextracto.

.. _architecture:

.. graphviz::

    digraph Wex {
        graph [rankdir=LR;fontname="Helvetica-Bold";fontsize=8];
        node [fixedsize=true;fontname="Helvetica-Bold";fontsize=12;width=1.0];
        Schedule -> Download [label=urls;fontcolor="#9A9A9A";fontsize=8];
        Wextracto [color=forestgreen;fontcolor=forestgreen];
        Download -> Wextracto [label=responses;fontcolor="#9A9A9A";fontsize=8];
        Wextracto -> Collate [label=data;fontcolor="#9A9A9A";fontsize=8];
        Wextracto -> Schedule [constraint=false;label=urls;fontcolor="#9A9A9A";fontsize=8];
    }


This architecture has these components:

    Schedule
      This component manages the URLs to be downloaded.
      The goal is to keep track which URLs you have downloaded and 
      which URLs you have yet to download.

    Download
      This component requests web pages and stores the responses for
      use by the *Wextracto* component.

    Wextracto
      This component reads the stored responses and extracts URLs and data.
      URLs are routed to the *Schedule* component.

    Collate
      This component receives data from the *Wextracto* component and 
      organizes it ready for use.  Organizing the data might involve
      storing it in a database.

Each of the other three components (*Schedule*, *Download* and *Collate*)
can be implemented in multiple ways depending on the requirements of the
crawl system.  Keeping just the core in Wextracto gives better
`seperation of concerns <http://en.wikipedia.org/wiki/Separation_of_concerns>`_


Interfaces
~~~~~~~~~~

In the :ref:`architecture <architecture>` diagram you can see Wextracto has three data flows.
One incoming (`responses`) and two outgoing (`urls` and `data`).


Responses
^^^^^^^^^

Although Wextracto can download and extract in one go, it is designed to be used
in system where the downloading is done separately from the extraction.

Having the download separate from extraction is generally helpful because:

  * it allows us to repeat the extraction process exactly for problem finding
  * it gives us easy access to large sample data sets
  * it can make the management of I/O in the system clearer

Wextracto can process responses that look like HTTP responses 
(headers then content).  For example:

.. code-block:: shell

        $ curl -D- http://httpbin.org/ip
        HTTP/1.1 200 OK
        Connection: keep-alive
        Server: gunicorn/18.0
        Date: Tue, 30 Dec 2014 19:32:18 GMT
        Content-Type: application/json
        Content-Length: 32
        Access-Control-Allow-Origin: *
        Access-Control-Allow-Credentials: true
        Via: 1.1 vegur

        {
          "origin": "67.180.76.235"
        }

Although most :mod:`extractors <wex.extractor>` will require the presence of a 
custom HTTP header, ``X-wex-request-url``, that contains the requested URL.
Any component preparing responses for processing using Wextracto should add 
this header.

A request can lead to multiple responses, each with their own URL.  In the
case where the response URL is not the same as the request URL an additional
header, ``X-wex-url``, that contains the responses URL.

Wextracto looks for responses such as these in files that have a ``.wexin``
extension.  It can also read a 
`.tar <http://en.wikipedia.org/wiki/Tar_%28computing%29>`_ file containing
files with the same extension.

URLs & Data
^^^^^^^^^^^

The handling of `urls` and `data` is described in the :mod:`reference <wex.output>`.
