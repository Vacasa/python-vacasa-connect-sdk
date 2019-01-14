"""Vacasa Connect Python SDK."""
import hashlib
import hmac
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

import pendulum
import requests
from retry.api import retry_call

logger = logging.getLogger(__name__)


def is_https_url(url: str) -> bool:
    return urlparse(url).scheme.lower() == 'https'


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
        if not is_https_url(endpoint):
            raise ValueError(f"`endpoint` scheme should be https")
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
            refresh_expiration = pendulum.parse(self._refresh_token['expires_at'])
            access_expiration = pendulum.parse(self._access_token['expires_at'])

            # refresh the token if it has expired
            if now > refresh_expiration or now > access_expiration:
                tokens = self._refresh_tokens()
                self._access_token = tokens.get('access_token')
                self._refresh_token = tokens.get('refresh_token')

    def _get_new_tokens(self) -> dict:
        """Generate new access and refresh tokens."""
        timestamp = int(pendulum.now().timestamp())
        payload = {
            'data': {
                'api_key': self.api_key,
                'timestamp': timestamp,
                'signature': self._generate_signature(timestamp)
            }
        }
        headers = {'content-type': 'application/json'}

        r = self._post(f"{self.endpoint}/auth", json=payload, headers=headers)
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
        r = self._post(url, json=payload)
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

    def _headers(self, language=None, currency=None) -> dict:
        """Build common headers."""
        self._populate_tokens()

        return {
            'Authorization': f"Bearer {self._access_token['token']}",
            'Accept-Language': self.language if language is None else language,
            'X-Accept-Currency': self.currency if currency is None else currency,
            'X-Accept-Timezone': self.timezone
        }

    def _generate_signature(self, timestamp: int) -> str:
        """Create a hash signature used for generating new tokens."""
        secret = bytes(self.api_secret, 'utf-8')
        message = f"{self.api_key}{timestamp}{self.api_secret}".encode('utf-8')

        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    @staticmethod
    def __get(url, headers: dict = None, params: dict = None):
        """HTTP GET request helper."""
        if headers is None:
            headers = {}

        r = requests.get(url, headers=headers, params=params)
        _handle_http_exceptions(r)

        return r

    def _get(self, url, headers: dict = None, params: dict = None, retry: bool = True):
        """HTTP Get helper with optional retrying."""
        if retry:
            return retry_call(
                self.__get,
                fargs=[url, headers, params],
                exceptions=requests.exceptions.RequestException,
                tries=5,
                delay=1,
                backoff=2
            )
        else:
            return self.__get(url, headers, params)

    @staticmethod
    def _post(url, data: dict = None, json: dict = None, headers: dict = None):
        """HTTP POST request helper."""
        if not headers:
            headers = {}

        r = requests.post(url, data=data, json=json, headers=headers)
        _handle_http_exceptions(r)

        return r

    def _ensure_url_has_host(self, url: str):
        """Insurance against the API returning a URL that lacks a host name"""
        parsed_url = urlparse(url)

        if not parsed_url.hostname:
            valid_host = urlparse(self.endpoint).hostname
            parsed_url = parsed_url._replace(netloc=valid_host)
            return urlunparse(parsed_url)

        return url

    def _iterate_pages(self, url: str, headers: dict, params: dict = None, *, retry=True):
        """Iterate over paged results."""
        more_pages = True

        while more_pages:
            r = self._get(url, headers=headers, params=params, retry=retry)
            yield from r.json()['data']

            if r.json().get('links', {}).get('next'):
                more_pages = True
                url = self._ensure_url_has_host(r.json()['links']['next'])
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

    def get_unit_by_id(self, unit_id: int, params: dict = None) -> dict:
        """Retrieve a single unit by its primary identifier.

        Args:
            unit_id: The unique identifier for the individual unit.
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.

        Returns:
            A dict containing attributes about the individual unit.
        """
        url = f"{self.endpoint}/v1/units/{unit_id}"
        r = self._get(url, headers=self._headers(), params=params)

        return r.json()['data']

    def get_unit_events(self,
                        unit_id: str = None,
                        created_since_time: str = None,
                        min_event_id: str = None,
                        include_units: bool = False,
                        include_unit_content: bool = False,
                        include_photos: bool = False,
                        include_amenities: bool = False):
        """Get a list of unit events. Optionally include unit data for units
           that have events in the response.

        Args:
            unit_id: Limit events to a single unit_id
            created_since_time: Limit events to those created after this timestamp
            min_event_id: Limit events to those starting with this event ID
            include_units: Whether or not to include unit data in the response
            include_unit_content: Whether or not to include unit content in the response
            include_photos: Whether or not to include unit photos (include_units must be True)
            include_amenities: Whether or not to include unit amenity data (include_units must be True)

        Returns:
            A dict containing the requested attributes related to unit-events. The event data will be
            returned in a 'data' key in each page. If include_units or include_unit_content is True
            that data will be returned in an 'included' key in each page.
        """
        url = f"{self.endpoint}/v1/unit-events"
        params = {}

        if unit_id:
            params['filter[unit_id]'] = unit_id

        if created_since_time:
            params['filter[created_at_min]'] = created_since_time

        if min_event_id:
            params['filter[event_min]'] = min_event_id

        if include_units:
            params['include'] = 'unit'

            if include_photos:
                params['include_meta'] = 'photos_list'

            if include_amenities:
                if 'include_meta' in params:
                    params['include_meta'] += ',amenities_map'
                else:
                    params['include_meta'] = 'amenities_map'

        if include_unit_content:
            if 'include' in params:
                params['include'] += ',unit-content'
            else:
                params['include'] = 'unit-content'

        # Custom paging because this endpoint returns responses in a different format than all others.
        more_pages = True
        yield_keys = ['data', 'included']

        while more_pages:
            r = self._get(url, headers=self._headers(), params=params)
            json_response = r.json()

            # Limiting the keys we return strips out the unnecessary paging links, etc.
            yield {k: json_response[k] for k in yield_keys if k in json_response}

            if json_response.get('links', {}).get('next'):
                more_pages = True
                url = self._ensure_url_has_host(json_response['links']['next'])
            else:
                more_pages = False

    def get_availability(self, params: dict = None):
        """Retrieve availabilities.

        Args:
            params: A dict containing a key for each query string parameter
                with a corresponding value. See https://connect.vacasa.com/
                for more detail.

        Yields:
            An iterator of availabilities. Each availability is a dict.
        """
        url = f"{self.endpoint}/v1/availability"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_availability_by_id(self, unit_id: int, params: dict = None):
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
                      params: dict = None,
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

    def get_amenities_groups(self, params: dict = None):
        """Retrieve a list of amenity groups

        Yields:
            An iterator of amenity groups. Each amenity group is a dict.
        """
        url = f"{self.endpoint}/v1/amenities-groups"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_amenities(self, params: dict = None):
        """Retrieve a list of all amenities for all units

        Yields:
            An iterator of unit amenities. Each unit amenity is a dict.
        """
        url = f"{self.endpoint}/v1/unit-amenities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_amenities_reduced(self, params: dict = None):
        """Retrieve a smaller subset of amenity attributes for all units

        Yields:
            An iterator of unit amenities. Each unit amenity is a dict.
        """
        url = f"{self.endpoint}/v1/unit-amenities-reduced"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_cities(self, params: dict = None):
        """Retrieve a list of all cities

        Yields:
            An iterator of cities. Each city is a dict.
        """
        url = f"{self.endpoint}/v1/cities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_states(self, params: dict = None):
        """Retrieve a list of all states

        Yields:
            An iterator of states. Each state is a dict.
        """
        url = f"{self.endpoint}/v1/states"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_countries(self, params: dict = None):
        """Retrieve a list of all countries

        Yields:
            An iterator of countries. Each country is a dict.
        """
        url = f"{self.endpoint}/v1/countries"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_destinations(self, params: dict = None):
        """Retrieve a list of all destinations

        Yields:
            An iterator of destinations. Each destination is a dict.
        """
        url = f"{self.endpoint}/v1/destinations"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_regions(self, params: dict = None):
        """Retrieve a list of all regions

        Yields:
            An iterator of regions. Each region is a dict.
        """
        url = f"{self.endpoint}/v1/regions"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_region_phones(self, params: dict = None):
        """Retrieve a list of all region-phones

        Yields:
            An iterator of region-phones. Each region-phone is a dict.
        """
        url = f"{self.endpoint}/v1/region-phones"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_region_cities(self, params: dict = None):
        """Retrieve a list of region-cities

        Yields:
            An iterator of region-cities. Each region-city is a dict.
        """
        url = f"{self.endpoint}/v1/region-cities"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_guarantees(self, params: dict = None):
        """Retrieve a list of guarantees

        Yields:
            An iterator of guarantees. Each guarantee is a dict.
        """
        url = f"{self.endpoint}/v1/guarantees"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_guarantee_dates(self, params: dict = None):
        """Retrieve a list of guarantee_dates

        Yields:
            An iterator of guarantee_dates. Each guarantee_date is a dict.
        """
        url = f"{self.endpoint}/v1/guarantee-dates"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_reviews(self, params: dict = None):
        """Retrieve a list of reviews

        Yields:
            An iterator of reviews. Each review is a dict.
        """
        url = f"{self.endpoint}/v1/reviews"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_reservations(self, params: dict = None):
        """Retrieve a list of reservations

        Yields:
            An iterator of reservations. Each reservation is a dict.
        """
        url = f"{self.endpoint}/v1/reservations"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_offices(self, params: dict = None, *, retry=False):
        """Retrieve a list of Vacasa local office locations

        Yields:
            An iterator of office locations. Each office location is a dict.
        """
        url = f"{self.endpoint}/v1/offices"
        headers = self._headers()

        return self._iterate_pages(url, headers, params, retry=retry)

    def get_page_templates(self, params: dict = None, *, retry=False):
        """Retrieve a list of Vacasa "pages" objects, which are html templates

        Yields:
            An iterator of pages.
        """
        url = f"{self.endpoint}/v1/pages"
        headers = self._headers()

        return self._iterate_pages(url, headers, params, retry=retry)

    @staticmethod
    def _trip_protection_to_integer(trip_protection: bool) -> int:
        """Convert from True/False/None to 1/0/-1"""
        if trip_protection is None:
            return 0
        return 1 if trip_protection else -1

    def get_quote(self,
                  unit_id: int,
                  arrival: str,
                  departure: str,
                  adults: int,
                  children: Optional[int] = 0,
                  pets: Optional[int] = 0,
                  trip_protection: Optional[bool] = None,
                  discount_id: Optional[int] = None,
                  language=None,
                  currency=None
                  ) -> dict:
        """ Get a price quote for a given stay

        Args:
            unit_id: A Vacasa Unit ID
            arrival: Checkin date in 'YYYY-MM-DD' format
            departure: Checkout date in 'YYYY-MM-DD' format
            adults: How many adults will be staying
            children: How many children will be staying
            pets: How many pets will be staying
            trip_protection: Has the user requested trip protection?
                -1 No
                 0 TBD
                 1 Yes
            discount_id: optional
            language: e.g. 'en-US' or 'es-ES' (optional)
            currency: e.g. 'USD' or 'EUR' (optional)

        Returns: dict

        """
        url = f"{self.endpoint}/v1/quotes"
        headers = self._headers(language, currency)

        params = {
            'adults': adults,
            'children': children,
            'pets': pets,
            'unit_id': unit_id,
            'arrival': arrival,
            'departure': departure,
        }

        if discount_id is not None:
            params['discount_id'] = discount_id

        params['trip_protection'] = self._trip_protection_to_integer(trip_protection)

        return self._get(url, headers, params, retry=False).json()

    def create_reservation(self,
                           unit_id: int,
                           arrival: str,
                           departure: str,
                           email: str,
                           address: dict,
                           adults: int,
                           quote_id: str,
                           first_name: str,
                           last_name: str,
                           account_number: str,
                           exp_mmyy: str,
                           cvv: Optional[str] = None,
                           phone: Optional[str] = None,
                           children: int = 0,
                           pets: int = 0,
                           trip_protection: Optional[bool] = None,
                           source: Optional[str] = None,
                           ) -> dict:
        """ Reserve a given unit

        Arguments:
            unit_id: A Vacasa Unit ID
            arrival: Checkin date in 'YYYY-MM-DD' format
            departure: Checkout date in 'YYYY-MM-DD' format
            email: User's email address
            phone: User's phone number
            address: User's address information, e.g.
                {
                    'address_1': '999 W Main St #301',
                    'city': 'Boise',
                    'state': 'ID',
                    'zip': '83702'
                }
            adults: How many adults will be staying
            children: How many children will be staying
            pets: How many pets will be staying
            trip_protection: Has the user requested trip protection?
                False: No
                None: TBD
                True: Yes
            quote_id: ID of a quote retrieved from the `GET /quotes` endpoint
            first_name: User's First Name (for billing)
            last_name: User's Last Name (for billing)
            account_number: Credit card #
            exp_mmyy: Credit card expiry in `mmyy` format
            cvv: Card verification value on credit card
            source: A Vacasa-issued code identifying the source of this request

        Returns: dict

        """

        url = f"{self.endpoint}/v1/reservations"
        headers = self._headers()
        payload = {
            'unit_id': unit_id,
            'arrival': arrival,
            'departure': departure,
            'email': email,
            'phone': phone,
            'address': address,
            'adults': adults,
            'children': children,
            'pets': pets,
            'trip_protection': trip_protection,
            'quote_id': quote_id,
            'first_name': first_name,
            'last_name': last_name,
            'account_number': account_number,
            'exp_mmyy': exp_mmyy,
            'source': source,
        }

        if phone is not None:
            payload['phone'] = phone

        payload['trip_protection'] = self._trip_protection_to_integer(trip_protection)

        if source is not None:
            payload['source'] = source

        if cvv:
            payload['cvv'] = str(cvv)

        return self._post(url, json={'data': {'attributes': payload}}, headers=headers).json()

    def created_cancelled_reservation(self,
                           unit_id: int,
                           arrival: str,
                           departure: str,
                           adults: int,
                           children: int,
                           pets: int,
                           trip_protection: bool,
                           discount_id: str,
                           first_name: str,
                           last_name: str,
                           phone: str,
                           rent: int,
                           fee_amount: int,
                           cleaning_fees: int,
                           trip_protection_fee: int,
                           total: int,
                           tax_amount: int,
                           ) -> dict:
        """
        Args:
            unit_id: A Vacasa Unit ID
            arrival: Checkin date in 'YYYY-MM-DD' format
            departure: Checkout date in 'YYYY-MM-DD' format
            adults: How many adults will be staying
            children: How many children will be staying
            pets: How many pets will be staying
            trip_protection: Has the user requested trip protection?
                -1 No
                0 TBD
                1 Yes
            discount_id:
            first_name:
            last_name:
            phone:
            rent:
            fee_amount:
            cleaning_fees:
            trip_protection_fee:
            total:
            tax_amount:

        Returns: dict

        """

        url = f"{self.endpoint}/v1/reservations-abandoned"
        headers = self._headers()
        payload = {
            'adults': adults,
            'first_night': arrival,
            'children': children,
            'cleaning_fees': cleaning_fees,
            'last_night': departure,
            'discount_id': discount_id,
            'fee_amount': fee_amount,
            'first_name': first_name,
            'last_name': last_name,
            'pets': pets,
            'phone': phone,
            'rent': rent,
            'tax_amount': tax_amount,
            'total': total,
            'trip_protection': self._trip_protection_to_integer(trip_protection),
            'trip_protection_fee': trip_protection_fee,
            'unit_id': unit_id,
        }

        return self._post(url, json={'data': {'attributes': payload}}, headers=headers).json()

    def create_blocklist_entry(self,
                               reservation_id: int,
                               first_name: str,
                               last_name: str,
                               email: str,
                               phone: str,
                               reason: str,
                               block: bool,
                               warn: bool) -> dict:
        """
        Args:
            reservation_id: A reservation id created when creating a canceled reservation.
            first_name:
            last_name:
            email:
            phone:
            reason: Reason for adding user to Vacasa's blocklist.
            block: 1 for iDology hard fail, else 0
            warn: 1 for iDology soft fail, else 0

        Returns: e.g.: {'result': 'success', 'id': 8411, 'meta': {'transaction_id': '5c393085ecd86'}}

        """

        url = f"{self.endpoint}/v1/blocklists"
        headers = self._headers()
        payload = {
            'reservation_id': reservation_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': phone,
            'reason': reason,
            'block': block,
            'warn': warn,
        }

        return self._post(url, json={'data': {'attributes': payload, 'type': 'blocklists'}}, headers=headers).json()


def _handle_http_exceptions(response):
    """Log 400/500s and raise them as exceptions"""
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        try:
            logger.exception(response.json())
        except ValueError:
            logger.exception(response.content)
        raise e
