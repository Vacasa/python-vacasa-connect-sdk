"""Vacasa Connect Python SDK."""
import backoff
import hashlib
import hmac
import json
import pendulum
import requests


class VacasaConnect:
    """This class serves as a wrapper for the Vacasa Connect API."""

    _access_token = None
    _refresh_token = None

    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 endpoint: str = 'https://connect.vacasa.com',
                 timezone: str = 'UTC',
                 language: str = 'en-US',
                 currency: str = 'USD'
                 ):
        """Initialize an instance of the VacasaConnect class.

        Args:
            api_key: Your Vacasa Connect API key.
            api_secret: Your Vacasa Connect API secret.
            endpoint: The URL of the Vacasa Connect API.
            timezone: UTC or a long-form version of a timezone from the tz
                database. Example: 'America/New_York'. See
                https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
                for more info.
            language: The language you will accept. If no localized content
                can be found, an error response is returned. Allowed format is
                {{ISO-639-1 Code}}-{{ISO 3166-1 Alpha-2 Code}}.
            currency: An ISO-4217 currency code. Send to request monetary
                values in this currency.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.endpoint = endpoint.rstrip('/')
        self.timezone = timezone
        self.language = language
        self.currency = currency
        self._populate_tokens()

    def _populate_tokens(self):
        """Decide if current tokens need refreshed and populate them."""
        # generate a token if we don't have one yet
        if self._access_token is None:
            tokens = self._get_new_tokens()
            self._access_token = tokens.get('access_token')
            self._refresh_token = tokens.get('refresh_token')
        else:
            now = pendulum.now()
            expiration = pendulum.parse(self._refresh_token['expires_at'])

            # refresh the token if it has expired
            if now > expiration:
                tokens = self._refresh_tokens()
                self._access_token = tokens.get('access_token')
                self._refresh_token = tokens.get('refresh_token')

    def _get_new_tokens(self) -> dict:
        """Generate new access and refresh tokens."""
        timestamp = int(pendulum.now().timestamp())
        payload = json.dumps({
            'data': {
                'api_key': self.api_key,
                'timestamp': timestamp,
                'signature': self._generate_signature(timestamp)
            }
        })
        headers = {'content-type': 'application/json'}

        r = self._post(f"{self.endpoint}/auth", payload, headers)
        tokens = r.json().get('data', {}).get('attributes', {})
        self._validate_tokens(tokens)

        return tokens

    def _refresh_tokens(self) -> dict:
        """Refresh existing tokens. Necessary when they expire."""
        url = f"{self.endpoint}/auth/refresh"
        payload = {
            'data': {
                'refresh_token': self._refresh_token['token']
            }
        }
        r = self._post(url, payload)
        tokens = r.json().get('data', {}).get('attributes', {})
        self._validate_tokens(tokens)

        return tokens

    @staticmethod
    def _validate_tokens(tokens):
        """Raise errors for incomplete tokens."""
        if 'access_token' not in tokens:
            raise LookupError("access_token not found")

        if 'refresh_token' not in tokens:
            raise LookupError("refresh_token not found")

    def _headers(self) -> dict:
        """Build common headers."""
        self._populate_tokens()

        return {
            'Authorization': f"Bearer {self._access_token['token']}",
            'Accept-Language': self.language,
            'X-Accept-Currency': self.currency,
            'X-Accept-Timezone': self.timezone
        }

    def _generate_signature(self, timestamp: int) -> str:
        """Create a hash signature used for generating new tokens."""
        secret = bytes(self.api_secret, 'utf-8')
        message = f"{self.api_key}{timestamp}{self.api_secret}".encode('utf-8')

        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    @staticmethod
    @backoff.on_exception(backoff.fibo,
                          requests.exceptions.RequestException, max_tries=5)
    def _get(url, headers: dict = None, params: dict = None):
        """HTTP GET request helper."""
        if headers is None:
            headers = {}

        if params is None:
            params = {}

        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()

        return r

    @staticmethod
    def _post(url, payload: dict, headers: dict = None):
        """HTTP POST request helper."""
        if not headers:
            headers = {}

        r = requests.post(url, data=payload, headers=headers)
        r.raise_for_status()

        return r

    def _iterate_pages(self, url: str, headers: dict, params: dict = None):
        """Iterate over paged results."""
        more_pages = True

        while more_pages:
            r = self._get(url, headers=headers, params=params)
            yield from r.json()['data']

            if r.json().get('links').get('next'):
                more_pages = True
                url = r.json()['links']['next']
            else:
                more_pages = False

    @staticmethod
    def _add_meta_param(params: dict, meta_value: str) -> dict:
        """Add to the include_meta comma-delimited string parameter."""
        meta_param = params.get('include_meta', '')
        # A leading comma is ignored by the connect api
        meta_param += f",{meta_value}"
        params['include_meta'] = meta_param

        return params

    @staticmethod
    def _add_include_param(params: dict, include_value: str) -> dict:
        """Add to the include_meta comma-delimited string parameter."""
        include_param = params.get('include', '')
        if include_param:
            include_param += ","
        include_param += f"{include_value}"
        params['include'] = include_param

        return params

    def get(self, uri, params: dict = None):
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/{uri}"
        r = self._get(url, headers=self._headers(), params=params)

        return r.json()

    def get_units(self,
                  params: dict = None,
                  include_photos: bool = False,
                  include_terminated: bool = False,
                  include_amenities: bool = False
                  ):
        """Retrieve multiple units.

        Args:
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.
            include_photos: Whether or not to include a list of photo URLs with
                each unit.
            include_terminated: Whether or not to include units that are
                currently terminated or pending termination.
            include_amenities: Whether or not to include key/values of each
                amenity with each unit.

        Yields:
            An iterator of units. Each unit is a dict.
        """
        if params is None:
            params = {}

        if include_photos:
            params = self._add_meta_param(params, 'photos_list')

        if include_amenities:
            params = self._add_meta_param(params, 'amenities_map')

        if not include_terminated:
            params['filter[terminated]'] = 0

        url = f"{self.endpoint}/v1/units"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_by_id(self, unit_id: str, params: dict = None) -> dict:
        """Retrieve a single unit by its primary identifier.

        Args:
            unit_id: The unique identifier for the individual unit.
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.

        Returns:
            A dict containing attributes about the individual unit.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/units/{unit_id}"
        r = self._get(url, headers=self._headers(), params=params)

        return r.json()['data']

    def get_availability(self, params: dict = None):
        """Retrieve availabilities.

        Args:
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.

        Yields:
            An iterator of availabilities. Each availability is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/availability"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_availability_by_id(self, unit_id: str, params: dict = None):
        """Retrieve availabilities for a single unit.

        Args:
            unit_id: The unique identifier for the individual unit.
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.

        Yields:
            An iterator of availabilities. Each availability is a dict.
        """
        if params is None:
            params = {}
        params['filter[unit_id]'] = unit_id

        return self.get_availability(params)

    def get_amenities(self,
                      params=None,
                      include_categories: bool = False,
                      include_content: bool = False,
                      include_options: bool = False
                      ):
        """Retrieve a master list of all amenities

        Yields:
            An iterator of amenities. Each amenity is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/amenities"
        headers = self._headers()

        if include_categories:
            params = self._add_include_param(params, 'categories')

        if include_content:
            params = self._add_include_param(params, 'content')

        if include_options:
            params = self._add_include_param(params, 'options')

        return self._iterate_pages(url, headers, params)

    def get_unit_amenities(self, params: dict = None):
        """Retrieve a list of all amenities for all units

        Yields:
            An iterator of unit amenities. Each unit amenity is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/unit-amenities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_amenities_reduced(self, params: dict = None):
        """Retrieve a smaller subset of amenity attributes for all units

        Yields:
            An iterator of unit amenities. Each unit amenity is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/unit-amenities-reduced"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_cities(self, params: dict = None):
        """Retrieve a list of all cities

        Yields:
            An iterator of cities. Each city is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/cities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_states(self, params: dict = None):
        """Retrieve a list of all states

        Yields:
            An iterator of states. Each state is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/states"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_countries(self, params: dict = None):
        """Retrieve a list of all countries

        Yields:
            An iterator of countries. Each country is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/countries"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_destinations(self, params: dict = None):
        """Retrieve a list of all destinations

        Yields:
            An iterator of destinations. Each destination is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/destinations"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_regions(self, params: dict = None):
        """Retrieve a list of all regions

        Yields:
            An iterator of regions. Each region is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/regions"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_region_phones(self, params: dict = None):
        """Retrieve a list of all region-phones

        Yields:
            An iterator of region-phones. Each region-phone is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/region-phones"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_region_cities(self, params: dict = None):
        """Retrieve a list of region-cities

        Yields:
            An iterator of region-cities. Each region-city is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/region-cities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_guarantees(self, params: dict = None):
        """Retrieve a list of guarantees

        Yields:
            An iterator of guarantees. Each guarantee is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/guarantees"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_guarantee_dates(self, params: dict = None):
        """Retrieve a list of guarantee_dates

        Yields:
            An iterator of guarantee_dates. Each guarantee_date is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/guarantee-dates"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_reviews(self, params: dict = None):
        """Retrieve a list of reviews

        Yields:
            An iterator of reviews. Each review is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/reviews"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_reservations(self, params: dict = None):
        """Retrieve a list of reservations

        Yields:
            An iterator of reservations. Each reservation is a dict.
        """
        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/reservations"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)
