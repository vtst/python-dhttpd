# python-dhttpd
An HTTP server that serves local files and act as a proxy for another
HTTP server.

Overview
========

python-dhttpd is a simple HTTP server, implemented on top of
[`BaseHTTPServer.HTTPServer`](https://docs.python.org/2/library/basehttpserver.html)
that serves files from a local directory (like
[`SimpleHTTPServer`](https://docs.python.org/2/library/simplehttpserver.html))
or by forwarding HTTP request to a delegate HTTP server.

For every GET or HEAD request, python-dhttpd first looks for a local
file to serve.  If a file is found, it is returned.  If not, the
request is forwarded to the delegate HTTP server.

Other types of HTTP requests are systematically forwarded.

Usage
=====

```
usage: dhttpd.py [-h] [--dserver HOST:PORT] [-p PORT] [-l DIR]

optional arguments:
  -h, --help            show this help message and exit
  --dserver HOST:PORT   Delegate HTTP server (default: localhost:8080)
  -p PORT, --port PORT  Port to listen (default: 8081)
  -l DIR, --localdir DIR
                        Local directory to serve
```

Using with App Engine devserver and Maven
=========================================

The Maven App Engine archetypes include a development server that
allows to run the App Engine application locally.  This development
server is automatically updated when Java classe files are modified.
However, it is *not* updated when static files (like HTML or
JavaScript files) are updated.

You can use python-dhttpd to work around this problem as follows:

```shell
cd <root-path-of-your-maven-project>
# Start the devserver
mvn appengine:devserver
# Start dhttpd
dhttpd.py --localdir=src/main/webapp
```

Then, access the App Engine application running on the devserver on
the port 8081 (instead of the default port 8080) by entering the
following address in your web browser:

```
http://localhost:8081/
```


License
=======

This software is distributed under the terms of the [Apache Software
License, version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

© Vincent Simonet, 2015.
