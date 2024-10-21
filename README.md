<p align="center">
    <img src="https://github.com/jpjacobpadilla/Stealth-Requests/blob/0572cdf58d141239e945a1562490b1d00054379c/logo.png?raw=true">
</p>

<h1 align="center">Stay Undetected While Scraping the Web.</h1>

### The All-In-One Solution to Web Scraping:
- **Realistic HTTP Requests:**
    - Mimics browser headers for undetected scraping, adapting to the requested file type
    - Tracks dynamic headers such as `Referer` and `Host`
    - Masks the TLS fingerprint of HTTP requests using the [curl_cffi](https://curl-cffi.readthedocs.io/en/latest/) package
- **Faster and Easier Parsing:**
    - Automatically extracts metadata (title, description, author, etc.) from HTML-based responses
    - Methods to extract all webpage and image URLs
    - Seamlessly converts responses into [Lxml](https://lxml.de/apidoc/lxml.html) and [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/) objects

### Install

```
$ pip install stealth_requests
```

### Sending Requests

Stealth-Requests mimics the API of the [requests](https://requests.readthedocs.io/en/latest/) package, allowing you to use it in nearly the same way.

You can send one-off requests like such:

```python
import stealth_requests as requests

resp = requests.get('https://link-here.com')
```

Or you can use a `StealthSession` object which will keep track of certain headers for you between requests such as the `Referer` header.

```python
from stealth_requests import StealthSession

with StealthSession() as session:
    resp = session.get('https://link-here.com')
```

When sending a request, or creating a `StealthSession`, you can specify the type of browser that you want the request to mimic - either `chrome`, which is the default, or `safari`. If you want to change which browser to mimic, set the `impersonate` argument, either in `requests.get` or when initializing `StealthSession` to `safari` or `chrome`.

### Sending Requests With Asyncio

This package supports Asyncio in the same way as the `requests` package:

```python
from stealth_requests import AsyncStealthSession

async with AsyncStealthSession(impersonate='safari') as session:
    resp = await session.get('https://link-here.com')
```

or, for a one-off request, you can make a request like this:

```python
import stealth_requests as requests

resp = await requests.get('https://link-here.com', impersonate='safari')
```

### Getting Response Metadata

The response returned from this package is a `StealthResponse`, which has all of the same methods and attributes as a standard [requests response object](https://requests.readthedocs.io/en/latest/api/#requests.Response), with a few added features. One of these extra features is automatic parsing of header metadata from HTML-based responses. The metadata can be accessed from the `meta` property, which gives you access to the following metadata:

- title: `str | None`
- author: `str | None`
- description: `str | None`
- thumbnail: `str | None`
- canonical: `str | None`
- twitter_handle: `str | None`
- keywords: `tuple[str] | None`
- robots: `tuple[str] | None`

Here's an example of how to get the title of a page:

```python
import stealth_requests as requests

resp = requests.get('https://link-here.com')
print(resp.meta.title)
```

### Parsing Responses

To make parsing HTML faster, I've also added two popular parsing packages to Stealth-Requests - Lxml and BeautifulSoup4. To use these add-ons you need to install the `parsers` extra: 

```
$ pip install stealth_requests[parsers]
```

To easily get an Lxml tree, you can use `resp.tree()` and to get a BeautifulSoup object, use the `resp.soup()` method.

For simple parsing, I've also added the following convenience methods, from the Lxml package, right into the `StealthResponse` object:

- `text_content()`: Get all text content in a response
- `xpath()` Go right to using XPath expressions instead of getting your own Lxml tree.

### Get All Image and Page Links From a Response

If you would like to get all of the webpage URLs (`a` tags) from an HTML-based response, you can use the `links` property. If you'd like to get all image URLs (`img` tags) you can use the `images` property from a response object.

```python
import stealth_requests as requests

resp = requests.get('https://link-here.com')
for image_url in resp.images:
    # ...
```


### Getting HTML Responses in Markdown Format

In some cases, it’s easier to work with a webpage in Markdown format rather than HTML. After making a GET request that returns HTML, you can use the `resp.markdown()` method to convert the response into a Markdown string, providing a simplified and readable version of the page content!

`markdown()` has two optional parameters:

1. `content_xpath` An XPath expression, in the form of a string, which can be used to narrow down what text is converted to Markdown. This can be useful if you don't want the header and footer of a webpage to be turned into Markdown.
2. `ignore_links` A boolean value that tells Html2Text whether it should include any links in the output of the Markdown.