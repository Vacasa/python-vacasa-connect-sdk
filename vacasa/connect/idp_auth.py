"""IDP Authentication for Vacasa Connect."""
import logging
import time
from typing import Optional

import jwt
from requests import HTTPError

from .requests_config import request_with_retries
from .util import log_http_error

logger = logging.getLogger(__name__)
requests = None


class IdpAuth:
    """This class handles authentication with the IDP server."""

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 idp_url: str = 'https://id.vacasa.com',
                 pool_connections: int = 10,
                 pool_maxsize: int = 10):
        """Initialize an instance of the IdpAuth class.

        Args:
            client_id: The client ID for the IDP server.
            client_secret: The client secret for the IDP server.
            idp_url: The URL of the IDP server.
            pool_connections: The number of connection pools to maintain (one per host).
            pool_maxsize: The maximum number of connections to keep in each pool (simultaneous connections per host).
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.idp_url = idp_url.rstrip('/')
        self._token = None
        self._token_expiry = 0

        global requests
        if requests is None:
            requests = request_with_retries(pool_connections=pool_connections, pool_maxsize=pool_maxsize)

    @property
    def token(self):
        """ Get the encoded JWT for use as a bearer token """
        if self._token is None:
            self._refresh_token()

        try:
            jwt._validate_exp(self._claims, self._leeway)
        except ExpiredSignatureError:
            self._refresh_token()

        return self._token

    def _get_config(self):
        """ Get configuration information from the discovery endpoint """
        r = requests.get(self.config_endpoint)
        log_http_error(r)
        self._config = r.json()

    def _get_token(self):
        """ Get a JWT from the IdP that we can use to connect to the ConnectAPI """
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': self._audience,
            'scope': ' '.join(self._scopes)
        }

        r = requests.post(self._config['token_endpoint'], json=data)
        log_http_error(r)
        self._token = r.json()['access_token']

    def _get_key(self):
        """ Get the public key info from the IdP so we can validate the JWT """
        r = requests.get(self._config['jwks_uri'])
        log_http_error(r)
        self._key = r.json()

    def _decode_token(self):
        """ Decode and validate the JWT """
        self._claims = jwt.decode(
            self._token,
            self._key,
            algorithms=self._config['id_token_signing_alg_values_supported'],
            audience=self._audience
        )

    def _refresh_token(self):
        """ Get new configuration information, token, and keys """
        self._get_config()
        self._get_token()
        self._get_key()
        self._decode_token()
