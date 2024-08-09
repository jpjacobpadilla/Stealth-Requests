import random
from urllib.parse import urlparse
from collections import defaultdict
from functools import partialmethod

from .response import StealthResponse

from curl_cffi.requests.session import Session
from curl_cffi.requests.models import Response


PROFILES = {
    'chrome124': [
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        },
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
            "sec-ch-ua-mobile": '?0',
            "sec-ch-ua-platform": '"macOS"'
        }
    ]
}


class StealthSession(Session):
    def __init__(
            self, 
            user_agent: str = None,
            impersonate: str = 'chrome124', 
            **kwargs
        ):
        if impersonate == 'chrome':
            impersonate = 'chrome124'

        self.profile = random.choice(PROFILES[impersonate])
        self.user_agent = user_agent
        self.last_request_url = defaultdict(lambda: 'https://www.google.com/')
        
        super().__init__(
            *args, 
            headers=self.initialize_headers(),
            impersonate=impersonate, 
            **kwargs
        )

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False

    def initialize_headers(self) -> dict[str, str]:
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.profile['User-Agent'],
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": self.profile['sec-ch-ua'],
            "sec-ch-ua-mobile": self.profile['sec-ch-ua-mobile'],
            "sec-ch-ua-platform": self.profile['sec-ch-ua-platform'],
        } 

    def get_dynamic_headers(self, url: str) -> dict[str, str]:
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        headers = {
            "Host": host,
            "Referer": self.last_request_url[host]
        }

        if self.user_agent:
            headers['User-Agent'] = self.user_agent

        self.last_request_url[host] = url
        return headers
        
    def request(self, method: str, url: str, *args, **kwargs) -> Response:
        headers = self.get_dynamic_headers(url) | kwargs.pop('headers', {})
        resp = super().request(method, url, *args, headers=headers, **kwargs)
        return StealthResponse(resp)
    
    head = partialmethod(request, "HEAD")
    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
    put = partialmethod(request, "PUT")
    patch = partialmethod(request, "PATCH")
    delete = partialmethod(request, "DELETE")
    options = partialmethod(request, "OPTIONS")
