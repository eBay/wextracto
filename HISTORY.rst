.. :changelog:

Release History
---------------

0.9.2 (2016-05-13)
++++++++++++++++++

  * Fix bug in handling HTML comments when fixing numeric character references


0.9.1 (2016-04-26)
++++++++++++++++++

  * Fix bug when using nested Cache objects


0.9.0 (2016-04-16)
++++++++++++++++++

  * Add support for reading WARC response format


0.8.8 (2016-04-11)
++++++++++++++++++

  * Fix bug in handling of invalid numeric character references


0.8.5 (2015-12-07)
++++++++++++++++++

  * Allow utf-8 in HTTP headers (only applies to PY2)


0.8.3 (2015-09-23)
++++++++++++++++++

  * Fix bug in HTTP decode caused by magic bytes handling.


0.8.2 (2015-09-21)
++++++++++++++++++

  * Add magic_bytes to Response for more reliable wex.http:decode behaviour.


0.7.9 (2015-08-18)
++++++++++++++++++

  * Re-worked encoding for HTML to pre-parse


0.7 (2015-06-04)
++++++++++++++++++

  * Better proxy support

0.4 (2015-02-12)
++++++++++++++++++

  * Now we flatten labels and values.
  * href and src become href_url and src_url.

0.3 (2014-12-29)
++++++++++++++++++

* Some API changes + switch to "tab-separated JSON".

0.2.2 (2014-10-24)
++++++++++++++++++

* Uploaded sdist to PyPI for "pip install wextracto" simplicity.

0.1 (2014-10-16)
++++++++++++++++++

* Initial release as open source
