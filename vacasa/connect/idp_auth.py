from jose import jwt, ExpiredSignatureError

from .requests_config import request_with_retries
from .util import log_http_error

requests = request_with_retries()


class IdpAuth:
    """Authorize with ConnectAPI using the Identity Provider Service (OIDC / JOSE)"""

    def __init__(self,
                 config_endpoint: str,
                 client_id: str,
                 client_secret: str,
                 audience: str,
                 scopes: list):
        self._token = None
        self._claims = None
        self._config = None
        self._key = None
        self.config_endpoint = config_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self._scopes = scopes
        self._audience = audience

    @property
    def token(self):
        """ Get the encoded JWT for use as a bearer token """
        if self._token is None:
            self._refresh_token()

        try:
            jwt._validate_exp(self._claims)
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
            algorithms=['RS256'],
            audience=self._audience
        )

    def _refresh_token(self):
        """ Get new configuration information, token, and keys """
        self._get_config()
        self._get_token()
        self._get_key()
        self._decode_token()
