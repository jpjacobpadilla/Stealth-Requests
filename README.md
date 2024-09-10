<p align="center">
    <img src="https://github.com/jpjacobpadilla/Stealth-Requests/blob/0572cdf58d141239e945a1562490b1d00054379c/logo.png?raw=true">
</p>

<h1 align="center">Stay Undetected While Scraping the Web.</h1>

### The All-In-One Solution to Web Scraping:
- Mimic the headers sent by a browser when going to a website (GET requests)
- Automatically handle and update the Referer header & client hint headers
- Mask the TLS fingerprint of the request using the [curl_cffi](https://curl-cffi.readthedocs.io/en/latest/) package
- Automatically parse the metadata from HTML responses such as page title, description, thumbnail, author, etc...
- Easily get an [lxml](https://lxml.de/apidoc/lxml.html) tree or [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/) object from the HTTP response. 

### Sending Requests

This package mimics the API of the `requests` package, and thus can be used in basically the same way.

You can send one-off requests like such:

```python
import stealth_requests and requests

resp = requests.get(link)
```

Or you can use a `StealthSession` object which will keep track of certain headers for you between requests such as the `Referer` header.

```python
from stealth_requests import StealthSession

with StealthSession() as s:
    resp = s.get(link)
```

When sending a one-off request, or creating a session, you can specify the type of browser that you want the request to mimic - either `safari` or `chrome` (which is the default).

### Sending Requests With Asyncio

This package supports Asyncio in the same way as the `requests` package.

```python
from stealth_requests import AsyncStealthSession

async with AsyncStealthSession(impersonate='chrome') as s:
    resp = await s.get(link)
```

or, for a one off request you can do something like this:

```python
from curl_cffi import requests

resp = await requests.post(link, data=...)
```

### Getting Response Metadata

The response returned from this package is a `StealthResponse` which has all of the same methods and attributes as a standard `requests` response, with a few added features. One if automatic parsing of header metadata. The metadata can be accessed from the `meta` attribute, which gives you access to the following data (if it's avaible on the scraped website):

- title: str
- description: str
- thumbnail: str
- author: str
- keywords: tuple[str]
- twitter_handle: str
- robots: tuple[str]
- canonical: str

Heres an example of how to get the title of a page:

```python
import stealth_requests and requests

resp = requests.get(link)
print(resp.meta.title)
```

### Parsing Response

To make parsing HTML easier, I've also added two popular parsing packages to this project - `Lxml` and `BeautifulSoup4`. To install these add-ons you need to install the parsers extra: `pip install stealth_requests[parsers]`.

To easily get an Lxml tree, you can use `resp.tree()` and to get a BeautifulSoup object, use the `resp.soup()` method.

For simple parsing, I've also added the following convience methods right to the `StealthResponse` object:

- `iterlinks` Iterate through all links in an HTML response
- `itertext`: Iterate through all text in an HTML response
- `text_content`: Get all text content in an HTML response
- `xpath` Go right to using XPATH expressions instead of getting your own Lxml tree.

### Getting HTML response in MarkDown format

Sometimes it's easier to get a webpage in MarkDown format instead of HTML. To do this, use the `resp.markdown()` method, after sending a GET request to a website.
