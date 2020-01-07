import logging
from typing import Optional
from urllib.parse import urlparse

import pendulum
from requests import Response, RequestException

logger = logging.getLogger(__name__)


def log_http_error(r: Response):
    """ Log any 4XX/5XX error responses and re-raise """
    try:
        r.raise_for_status()
    except RequestException as e:
        log_level = logging.INFO if r.status_code < 500 else logging.ERROR
        try:
            logger.log(log_level, r.json())
        except ValueError:
            logger.log(log_level, r.content)
        raise e


def is_https_url(url: str) -> bool:
    return urlparse(url).scheme.lower() == 'https'


def subtract_days(start_date: str, days: int) -> Optional[str]:
    """Subtract the specified number of days from the supplied date string

    Args:
        start_date: The date to subtract from in YYYY-MM-DD format
        days: The number of days to subtract

    Returns:
        The resulting date in YYYY-MM-DD format
    """
    try:
        dt = pendulum.from_format(start_date, 'YYYY-MM-DD')
    except ValueError:
        return None

    return dt.subtract(days=days).to_date_string()
