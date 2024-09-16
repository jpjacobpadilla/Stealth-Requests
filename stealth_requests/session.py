import os
import json
import random
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse
from collections import defaultdict
from functools import partialmethod

from .response import StealthResponse

from curl_cffi.requests.session import Session, AsyncSession
from curl_cffi.requests.models import Response


SUPPORTED_IMAGE_EXTENSIONS = [
    'jpeg', 'jpg', 'png', 'gif', 
    'bmp', 'webp', 'ico', 'svg', 
    'tiff', 'heic', 'heif'
]
CSS_EXTENSION = 'css'

CHROME_MEDIA_TYPES = {
    'image': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'document': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'css': 'text/css,*/*;q=0.1',
}
SAFARI_IMAGE_TYPES = {
    'image': 'image/webp,image/avif,image/jxl,image/heic,image/heic-sequence,video/*;q=0.8,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
    'document': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'css': 'text/css,*/*;q=0.1',
}


@dataclass
class ClientProfile:
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str


class BaseStealthSession:
    def __init__(
            self, 
            client_profile: str = None,
            impersonate: str = 'chrome124', 
            **kwargs
        ):
        if impersonate.lower() in ('chrome', 'chrome124'):
            impersonate = 'chrome124'
            self.media_type_sets = CHROME_MEDIA_TYPES

        elif impersonate.lower() in ('safari', 'safari_17_0', 'safari17'):
            impersonate = 'safari17_0'
            self.media_type_sets = SAFARI_IMAGE_TYPES

        self.profile = client_profile or BaseStealthSession.create_profile(impersonate)
        self.last_request_url = defaultdict(lambda: 'https://www.google.com/')
        
        super().__init__(
            headers=self.initialize_chrome_headers() 
                if impersonate == 'chrome124' 
                else self.initialize_safari_headers(),
            impersonate=impersonate, 
            **kwargs
        )
    
    @staticmethod
    def create_profile(impersonate: str) -> ClientProfile:
        file_path = os.path.join(os.path.dirname(__file__), 'profiles.json')

        with open(file_path, encoding='utf-8', mode='r') as file:
            user_agents = json.load(file)

        assert impersonate in user_agents.keys(), f'Please choose one of the supported profiles: {user_agents.keys()}'

        return ClientProfile(
            user_agent=random.choice(user_agents[impersonate]),
            sec_ch_ua='"Not A;Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"' if impersonate == 'chrome_124' else None,
            sec_ch_ua_mobile='?0' if impersonate == 'chrome_124' else None,
            sec_ch_ua_platform='"macOS"' if impersonate == 'chrome_124' else None
        )
        
    def initialize_chrome_headers(self) -> dict[str, str]:
        return {
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.profile.user_agent,
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "sec-ch-ua": self.profile.sec_ch_ua,
            "sec-ch-ua-mobile": self.profile.sec_ch_ua_mobile,
            "sec-ch-ua-platform": self.profile.sec_ch_ua_platform,
        } 

    def initialize_safari_headers(self) -> dict[str, str]:
        return {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": self.profile.user_agent
        } 

    def get_media_types(self, url: str) -> str:
        path = Path(urlparse(url).path)
        extension = path.suffix.removeprefix('.').lower()

        if extension:
            if extension in SUPPORTED_IMAGE_EXTENSIONS:
                return self.media_type_sets['image']
            if extension in CSS_EXTENSION:
                return self.media_type_sets['css']

        return self.media_type_sets['document']

    def get_dynamic_headers(self, url: str) -> dict[str, str]:
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        headers = {
            "Accept": self.get_media_types(url),
            "Host": host,
            "Referer": self.last_request_url[host]
        }

        self.last_request_url[host] = url
        return headers


class StealthSession(BaseStealthSession, Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def request(self, method: str, url: str, *args, **kwargs) -> Response:
        headers = self.get_dynamic_headers(url) | kwargs.pop('headers', {})
        resp = Session.request(self, method, url, *args, headers=headers, **kwargs)
        return StealthResponse(resp)
    
    head = partialmethod(request, "HEAD")
    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
    put = partialmethod(request, "PUT")
    patch = partialmethod(request, "PATCH")
    delete = partialmethod(request, "DELETE")
    options = partialmethod(request, "OPTIONS")

class AsyncStealthSession(BaseStealthSession, AsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def request(self, method: str, url: str, *args, **kwargs) -> Response:
        headers = self.get_dynamic_headers(url) | kwargs.pop('headers', {})
        resp = await AsyncSession.request(self, method, url, *args, headers=headers, **kwargs)
        return StealthResponse(resp)
    
    head = partialmethod(request, "HEAD")
    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
    put = partialmethod(request, "PUT")
    patch = partialmethod(request, "PATCH")
    delete = partialmethod(request, "DELETE")
    options = partialmethod(request, "OPTIONS")
