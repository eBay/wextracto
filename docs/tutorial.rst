.. _tutorial:

########
Tutorial
########

Introduction
~~~~~~~~~~~~

This tutorial shows you how to use Wextracto to extract data from an HTML web
page.

To work through the tutorial you need to download and install
`Python <https://www.python.org/downloads/>`_.

You also need to install Wextracto.  If you can, you should install it
into a
`virtual environment <http://virtualenv.readthedocs.org/en/latest/virtualenv.html>`_
because this makes things easier to manage.
The recommended way to install Wextracto is using
`pip <https://pip.pypa.io/en/latest/installing.html>`_:

.. code-block:: shell

    $ pip install Wextracto

This will install the ``wex`` command:

.. code-block:: shell

    $ wex --help

You are now ready to begin the tutorial.


Writing A Minimal Extractor
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An extractor is a function that takes an HTTP response as a parameter and
returns (or yields) values extracted from it.  Our extractor is going to 
return the URL of the response.  Write or copy the following into a file 
called ``tutorial.py``:

.. literalinclude:: samples/tutorial/step1/tutorial.py

The ``response`` parameter here is 
file-like object of the type used by the standard library
`urllib2 <https://docs.python.org/2/library/urllib2.html#urllib2.urlopen>`_.

Now we need to tell the ``wex`` command about our new extractor.  We do this
by creating a file called ``entry_points.txt`` with the following contents:

.. literalinclude:: samples/tutorial/step1/entry_points.txt

Now run ``wex`` with the following URL:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    "http://gilessbrown.github.io/cheeses/cheddar.html"

Congratulations, you have just written an extractor!

.. _xpath-expressions:

XPath Expressions
~~~~~~~~~~~~~~~~~

Python has a great library for processing XML and HTML data called 
`lxml <http://lxml.de/>`_.  We can use this library in our extractor.

Let's use a simple `XPath <http://en.wikipedia.org/wiki/XPath>`_ expression 
to get some text from our chosen web page.  Edit ``tutorial.py`` to look
like this:

.. literalinclude:: samples/tutorial/step2/tutorial.py

Now re-run ``wex`` with the same URL we used previously:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    ["\n\t\t\tCheddar\n\t\t"]

You may be wondering about the square brackets around the text.  That is 
because ``wex`` serializes values using 
`JSON <http://en.wikipedia.org/wiki/JSON>`_.  
Our XPath expression returns a Python list which gives us the square brackets
in JSON.

You may also have noticed the leading and trailing whitespace.  We'll look
at how to get rid of that in the next section.


Normalized Text
~~~~~~~~~~~~~~~

Probably the most common pattern for an extractor is that we have an XPath (or 
`CSS <http://lxml.de/cssselect.html#the-cssselector-class>`_) selector to
select exactly one HTML element and then you want the space-normalized text 
inside that element and any sub-elements.  Space-normalized means runs of 
whitespace are converted into a single space character and leading and 
trailing whitespace is trimmed.

Wextracto provides functions to do exactly that.  Here is what our extractor now looks like:

.. literalinclude:: samples/tutorial/step3/tutorial.py

The :func:`text <wex.etree.text>` function returns the normalized text from each selectedelement.  The :class:`one <wex.iterable.one>` function ensures there is exactly one selected element.

Let's run ``wex`` with the usual URL again to check the result:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    "Cheddar"

That's much tidier!

You may be wondering why we don't just use the XPath
`normalize-space <https://developer.mozilla.org/en-US/docs/Web/XPath/Functions/normalize-space>`_
function.  The reason is that when our extractor encounters a page where it 
extracts multiple elements then ``normalize-space()`` would
silently take the text from the first element.  This is bad news because we
want our extractors to fail loudly if things are not the way we expect.


.. _multiple-values:

Multiple Values
~~~~~~~~~~~~~~~

Often we want to extract multiple values from our web page.  This is done by 
`yield`-ing values instead `return`-ing a single value.

So that we know which value is which we also label the values by yielding
a name for the value at the same time.

Modify ``tutorial.py`` to yield the names and values:

.. literalinclude:: samples/tutorial/step4/tutorial.py

Now re-run ``wex``:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    "name"	"Cheddar"
    "country"	"England"
    "region"	"Somerset"

Wextracto uses the tab character to separate the label from the value.

Errors
~~~~~~

Yielding multiple values from an extractor is ok if all the values
extract successfully.  Unfortunately, if they don't, we don't get the
remaining values even if they would have extracted successfully.

Let's extend the extractor we wrote in the previous section and add a new 
attribute.  This time let's deliberately make a mistake so we can see what
happens:

.. literalinclude:: samples/tutorial/step5/tutorial.py

Now re-run ``wex``:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    "name"	"Cheddar"
    #ZeroDivisionError('integer division or modulo by zero',)!

The ``#`` and ``!`` at the start and end of that final line is Wextracto's 
way of telling us that we ended up with a value that was not JSON encodable. 
In this case because there was a ZeroDivisionError exception.

Notice how we didn't see more values following the exception.

What we'd really like is for each attribute to be extracted in such a way
that an exception while extracting one attribute doesn't mean the others
don't get extracted.

To make that happen we'll need each attribute to be extracted in its own
function.  In the next section we'll see how Wextracto helps you do that.

.. _attributes:

Attributes
~~~~~~~~~~

Wextracto provides an class specifically for extracting named attributes 
and it is called :class:`wex.extractor.Attributes`.  This class lets you 
create a collection of extractors each of which has a name.  The class 
instance is itself callable it it yields the results of each extractor in 
the collection together with its name.

Extractors can be added to the collection by 
`decorating <https://docs.python.org/2/whatsnew/2.4.html?highlight=decorator#pep-318-decorators-for-functions-and-methods>`_ them with the collections ``.attribute`` method.

So let's use the :class:`wex.extractor.Attributes` class.  

Copy the code from here:

.. literalinclude:: samples/tutorial/step6/tutorial.py

You may notice that we have switched from calling ``.xpath()`` on the
element tree to using the ``wex.etree.xpath`` function.  The function produce
by calling this function knows when to parse the response so we don't need to
organize that.

Let's try running our extractor now and see what we get:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html
    "country"	"England"
    "whoops"	#ZeroDivisionError('integer division or modulo by zero',)!
    "region"	"Somerset"
    "name"	"Cheddar"

Now we've got something for all of the attributes we wanted and it tells
which attribute extractor isn't working.


Composing Attributes
~~~~~~~~~~~~~~~~~~~~

If you need to write a lot of extractors then you may find that the using
the decorator syntax for :class:`wex.extractor.Attributes` leads to a lot of
boilerplate code.  Fortunately there is an alternative.

If you look at the examples in the :ref:`previous section <attributes>`, 
you will see that the extractors (apart from ``whoops``) all look 
something like:

.. code-block:: python

    def xyz(response):
        return text(xpath(...)(response))

It turns out this kind of pattern is very common in writing extractors.
A technique called
`function composition <http://en.wikipedia.org/wiki/Function_composition_%28computer_science%29>`_
lets us define these extractor functions very succinctly.

In Wextracto function composition is performed with the ``|`` operator
(like Unix pipes).

So we can define the extractor above as:

.. code-block:: python

    xyz = xpath(...) | text

We can pass these composed functions directly into the constructor for
`wex.extractor.Attributes` and get something that looks like:

.. literalinclude:: samples/tutorial/step7/tutorial.py

As you can see, this is a very compact representation for simple extractors.

.. _labelling:

Labelling
~~~~~~~~~

So far we've only been extracting data from one web page, but eventually
we'd like to move on to extracting from multiple pages.  Let's see what
happens:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html http://gilessbrown.github.io/cheeses/brie.html
    "country"	"tEngland"
    "region"	"Somerset"
    "name"	"Cheddar"
    "country"	"France"
    "region"	"Seine-et-Marne"
    "name"	"Brie"

Oh dear.  It isn't very clear which value came from which web page.

We can fix this by using the :func:`wex.extractor.label` function:

.. literalinclude:: samples/tutorial/step8/tutorial.py

The code here is going to label the output with the URL of the current
response.

Let's try it:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/cheddar.html http://gilessbrown.github.io/cheeses/brie.html
    "http://gilessbrown.github.io/cheeses/cheddar.html"	"country"	"England"
    "http://gilessbrown.github.io/cheeses/cheddar.html"	"region"	"Somerset"
    "http://gilessbrown.github.io/cheeses/cheddar.html"	"name"	"Cheddar"
    "http://gilessbrown.github.io/cheeses/brie.html"	"country"	"France"
    "http://gilessbrown.github.io/cheeses/brie.html"	"region"	"Seine-et-Marne"
    "http://gilessbrown.github.io/cheeses/brie.html"	"name"	"Brie"

As before, the labels are tab delimited.


Multiple Entities
~~~~~~~~~~~~~~~~~

In the :ref:`labelling` section we saw how we can label values with the URL
from which they came, but sometimes you get multiple entities on the same
web page and they each have their own set of attributes.

Let's try our extractor on that kind of page:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/gloucester.html
    "http://gilessbrown.github.io/cheeses/gloucester.html"  "country"       #MultipleValuesError()!
    "http://gilessbrown.github.io/cheeses/gloucester.html"  "region"        #MultipleValuesError()!
    "http://gilessbrown.github.io/cheeses/gloucester.html"  "name"  #MultipleValuesError()!

Oh dear.  What can we do?  Well if we visit that web page in a browser and 
`view the source <view-source:http://gilessbrown.github.io/cheeses/gloucester.html>`_
we find that each ``<h1>`` helpfully has a International Cheese 
Identification Number (ICIN) as an attribute.

So what we can do is re-write the extractor to visit each ``<h1>``
and extract the data we want relative to that element.

Here is what the code looks like:

.. literalinclude:: samples/tutorial/step9/tutorial.py

And then we run ``wex``:

.. code-block:: shell

    $ wex http://gilessbrown.github.io/cheeses/gloucester.html
    "SNGGLCD7DDFD41"	"country"	"England"
    "SNGGLCD7DDFD41"	"region"	"Gloucestershire"
    "SNGGLCD7DDFD41"	"name"	"Single Gloucester"
    "DBLGLCCECAA22C"	"country"	"England"
    "DBLGLCCECAA22C"	"region"	"Gloucestershire"
    "DBLGLCCECAA22C"	"name"	"Double Gloucester"

What Next?
~~~~~~~~~~

    * Read the :ref:`userguide`.
    * Read the `source code <https://github.com/eBay/wextracto>`_.
