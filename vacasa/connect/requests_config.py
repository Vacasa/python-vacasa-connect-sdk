import random

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RETRY_STATUS_CODES = (500, 502, 503, 504)


class BackoffWithJitter:
    """urllib3.util.retry.Retry expects a float for `backoff_factor`, but we want to sneak in some jitter """

    def __init__(self, backoff, jitter_min, jitter_max):
        self._backoff = backoff
        self._jitter = (jitter_min, jitter_max)

    def __mul__(self, other):
        """Add some random jitter every time the backoff function tries to do some multiplication"""
        return (self._backoff + random.uniform(*self._jitter)) * other


def request_with_retries(retries=5,
                         backoff_factor=BackoffWithJitter(.25, 0, .25),
                         status_forcelist=RETRY_STATUS_CODES,
                         raise_on_status=False,
                         raise_on_redirect=False,
                         ) -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=raise_on_status,
        raise_on_redirect=raise_on_redirect,
    ))
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
