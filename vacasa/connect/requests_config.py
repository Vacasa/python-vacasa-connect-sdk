import logging
import random

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

RETRY_STATUS_CODES = (500, 502, 503, 504)

logger = logging.getLogger(__name__)


class RetryWithJitter(Retry):
    """ urllib3.util.retry.Retry doesn't do jitter with `backoff_factor` so we'll add it here """

    def __init__(self, jitter=None, *args, **kwargs):
        self._jitter = jitter
        super().__init__(*args, **kwargs)

    def get_backoff_time(self):
        value = super().get_backoff_time()
        if self._jitter is not None:
            return value + random.uniform(*self._jitter)
        return value

    def increment(self, *args, **kwargs):
        """ Add a log message every time the retry backoff happens """
        next_retry = super().increment(*args, **kwargs)

        log_message = {
            "message": "Retryable HTTP error, backing off.",
            "num_retries": len(next_retry.history),
            "retries_remaining": next_retry.total,
        }

        try:
            response = kwargs['response']
            log_message['response'] = {
                'status': response.status,
                'reason': response.reason,
                'body': response.data,
            }
        except (KeyError, AttributeError):
            pass

        logger.debug(log_message)

        return next_retry


def request_with_retries(retry_config: Retry = None, pool_connections: int = 10, pool_maxsize: int = 10) -> requests.Session:
    """ Requests initiated with the resulting session should retry server/connection errors with backoff and jitter """
    if retry_config is None:
        retry_config = RetryWithJitter(
            total=5,
            connect=5,
            read=5,
            backoff_factor=.25,
            jitter=(0, .25),
            status_forcelist=RETRY_STATUS_CODES,
            raise_on_status=False,
            raise_on_redirect=False,
        )

    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_config, pool_connections=pool_connections, pool_maxsize=pool_maxsize)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
