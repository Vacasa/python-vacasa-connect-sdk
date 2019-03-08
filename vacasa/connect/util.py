import logging
from urllib.parse import urlparse

from requests import Response, RequestException

logger = logging.getLogger(__name__)


def log_http_error(r: Response):
    """ Log any 4XX/5XX error responses and re-raise """
    try:
        r.raise_for_status()
    except RequestException as e:
        try:
            logger.exception(r.json())
        except ValueError:
            logger.exception(r.content)
        raise e


def is_https_url(url: str) -> bool:
    return urlparse(url).scheme.lower() == 'https'
