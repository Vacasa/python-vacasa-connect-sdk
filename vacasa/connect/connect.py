"""Vacasa Connect Python SDK."""
import logging
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from .idp_auth import IdpAuth
from .requests_config import request_with_retries
from .util import log_http_error, is_https_url

logger = logging.getLogger(__name__)
requests = request_with_retries()


class VacasaConnect:
    """This class serves as a wrapper for the Vacasa Connect API."""

    def __init__(self,
                 auth: IdpAuth,
                 endpoint: str = 'https://connect.vacasa.com',
                 timezone: str = 'UTC',
                 language: str = 'en-US',
                 currency: str = 'USD',
                 ):
        """Initialize an instance of the VacasaConnect class.

        Args:
            auth: IdpAuth setup object
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
            raise ValueError("`endpoint` scheme must be https")

        self._auth = auth
        self.endpoint = endpoint.rstrip('/')
        self.timezone = timezone
        self.language = language
        self.currency = currency

    def _headers(self, language=None, currency=None) -> dict:
        """Build common headers."""
        return {
            'Authorization': f"Bearer {self._auth.token}",
            'Accept-Language': self.language if language is None else language,
            'X-Accept-Currency': self.currency if currency is None else currency,
            'X-Accept-Timezone': self.timezone
        }

    @staticmethod
    def _get(url, headers: dict = None, params: dict = None):
        """HTTP GET request helper."""
        if headers is None:
            headers = {}

        r = requests.get(url, headers=headers, params=params)
        log_http_error(r)

        return r

    @staticmethod
    def _post(url, data: dict = None, json: dict = None, headers: dict = None):
        """HTTP POST request helper."""
        if not headers:
            headers = {}

        r = requests.post(url, data=data, json=json, headers=headers)
        log_http_error(r)

        return r

    def _ensure_url_has_host(self, url: str):
        """Insurance against the API returning a URL that lacks a host name"""
        parsed_url = urlparse(url)

        if not parsed_url.hostname:
            valid_host = urlparse(self.endpoint).hostname
            parsed_url = parsed_url._replace(netloc=valid_host)
            return urlunparse(parsed_url)

        return url

    def _iterate_pages(self, url: str, headers: dict, params: dict = None):
        """Iterate over paged results."""
        more_pages = True

        while more_pages:
            r = self._get(url, headers=headers, params=params)
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

    def get_offices(self, params: dict = None):
        """Retrieve a list of Vacasa local office locations

        Yields:
            An iterator of office locations. Each office location is a dict.
        """
        url = f"{self.endpoint}/v1/offices"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_page_templates(self, params: dict = None):
        """Retrieve a list of Vacasa "pages" objects, which are html templates

        Yields:
            An iterator of pages.
        """
        url = f"{self.endpoint}/v1/pages?include=content"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_quote(self,
                  unit_id: int,
                  arrival: str,
                  departure: str,
                  adults: int,
                  children: int = 0,
                  pets: int = 0,
                  trip_protection: bool = None,
                  discount_id: int = None,
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
                False: No
                None: TBD
                True: Yes
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

        params['trip_protection'] = _trip_protection_to_integer(trip_protection)

        return self._get(url, headers, params).json()

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
                           cvv: str = None,
                           phone: str = None,
                           children: int = 0,
                           pets: int = 0,
                           trip_protection: bool = None,
                           source: str = None,
                           discount_id: int = None,
                           initial_payment_amount: float = None,
                           anonymous_id: str = None,
                           terms: str = None
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
            discount_id: Must match value from `quote_id`
            initial_payment_amount: if included, only process this amount
                initially, the remaining balance will be charged according to
                payment plan logic (i.e. 30 days before check-in)
            anonymous_id (optional): UUID4 for tracking,
            terms: An ISO 8601 timestamp capturing the point in time where a
                user accepted the rental terms.
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

        payload['trip_protection'] = _trip_protection_to_integer(trip_protection)

        if source is not None:
            payload['source'] = source

        if cvv:
            payload['cvv'] = str(cvv)

        if discount_id:
            payload['discount_id'] = discount_id

        if initial_payment_amount:
            payload['initial_payment_amount'] = initial_payment_amount

        if anonymous_id is not None:
            if _is_uuid4(anonymous_id):
                payload['anonymous_id'] = anonymous_id
            else:
                logger.warning("Ignoring invalid UUID4: %s", anonymous_id)

        if terms is not None:
            payload['terms'] = terms

        return self._post(url, json={'data': {'attributes': payload}}, headers=headers).json()

    def create_cancelled_reservation(self,
                                     unit_id: int,
                                     arrival: str,
                                     departure: str,
                                     email: str,
                                     adults: int,
                                     children: int,
                                     pets: int,
                                     first_name: str,
                                     last_name: str,
                                     phone: str,
                                     rent: float,
                                     fee_amount: float,
                                     cleaning_fees: float,
                                     trip_protection_fee: float,
                                     total: float,
                                     tax_amount: float,
                                     trip_protection: bool = None,
                                     discount_id: str = None,
                                     source: str = None,
                                     anonymous_id: str = None,
                                     cancellation_reason: str = None
                                     ) -> dict:
        """
        Args:
            unit_id: A Vacasa Unit ID
            arrival: Checkin date in 'YYYY-MM-DD' format
            departure: Checkout date in 'YYYY-MM-DD' format
            email: User's email address
            adults: How many adults will be staying
            children: How many children will be staying
            pets: How many pets will be staying
            trip_protection: Has the user requested trip protection?
                False: No
                None: TBD
                True: Yes
            discount_id: Must match value from `quote_id`
            first_name: User's first name (for billing)
            last_name: User's last name (for billing)
            phone: User's phone number
            rent: Cost of rent
            fee_amount: Cost of fees
            cleaning_fees: Cost of cleaning fees
            trip_protection_fee: Cost of trip protection
            total: Total code
            tax_amount: Cost of taxes
            source: A Vacasa-issued code identifying the source of this request
            anonymous_id (optional): UUID4 for tracking

        Returns: dict

        """

        url = f"{self.endpoint}/v1/reservations-abandoned"
        headers = self._headers()
        payload = {
            'adults': adults,
            'first_night': arrival,
            'children': children,
            'email': email,
            'cleaning_fees': cleaning_fees,
            'last_night': departure,
            'fee_amount': fee_amount,
            'first_name': first_name,
            'last_name': last_name,
            'pets': pets,
            'phone': phone,
            'rent': rent,
            'tax_amount': tax_amount,
            'total': total,
            'trip_protection': _trip_protection_to_integer(trip_protection),
            'trip_protection_fee': trip_protection_fee,
            'unit_id': unit_id,
        }

        if discount_id:
            payload['discount_id'] = discount_id

        if source is not None:
            payload['source'] = source

        if cancellation_reason is not None:
            payload['cancellation_reason'] = cancellation_reason

        if anonymous_id is not None:
            if _is_uuid4(anonymous_id):
                payload['anonymous_id'] = anonymous_id
            else:
                logger.warning("Ignoring invalid UUID4: %s", anonymous_id)

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
            first_name: User's first name (for billing)
            last_name: User's last name (for billing)
            email: User's email address
            phone: User's phone number
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
            'block': _convert_bool_to_int(block),
            'warn': _convert_bool_to_int(warn),
        }

        return self._post(url, json={'data': {'attributes': payload, 'type': 'blocklists'}}, headers=headers).json()

    def get_blocklist_entries(self, page_number=0) -> dict:
        """
        Args:
            page_number: An int used to specify a page of blocklist data.

        Returns: dict
        """

        url = f"{self.endpoint}/v1/blocklists"
        if page_number:
            url += "?page[number]=" + str(page_number)
        headers = self._headers()

        return self._get(url, headers=headers).json()

    def add_reservation_guests(self,
                               reservation_id: int,
                               first_name: str,
                               last_name: str,
                               email: str) -> dict:
        """
        Args:
            reservation_id: A reservation id created when creating a canceled reservation.
            first_name:
            last_name:
            email:

        Returns: json response for success

        """

        url = f"{self.endpoint}/v1/reservation-guests"
        headers = self._headers()
        payload = {
            'reservation_id': reservation_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

        return self._post(url, json={'data': {'attributes': payload,
                                              'type': 'reservation-guest'}}, headers=headers).json()

    def add_identity_check(self,
                           reservation_id: int,
                           idology_check_id: str,
                           unit_id: int,
                           first_name: str,
                           last_name: str,
                           address: str,
                           email: str,
                           phone: str,
                           zip: str,
                           blocklist_id: int = None,
                           passed_initial_check: bool = None,
                           differentiator_shown: bool = None,
                           questions_quantity: int = None,
                           questions_correct: int = None,
                           challenge_quantity: int = None,
                           challenge_correct: int = None,
                           received_soft_fail: bool = None,
                           received_hard_fail: bool = None,
                           approved_for_checkout: bool = None,
                           idology_check_message: str = None,
                           ):
        """
        Adds an identity record into the monolith for idology check result
        """
        url = f"{self.endpoint}/v1/identity-checks"
        headers = self._headers()
        payload = {
            'code_id': 138,
            'reservation_id': reservation_id,
            'external_reference_id': idology_check_id,
            'external_response_message': idology_check_message,
            'unit_id': unit_id,
            'first_name': first_name,
            'last_name': last_name,
            'address': address,
            'email': email,
            'phone': phone,
            'zip': zip,
            'passed_initial_check': _convert_bool_to_int(passed_initial_check),
            'differentiator_shown': _convert_bool_to_int(differentiator_shown),
            'questions_quantity_shown': questions_quantity,
            'questions_quantity_correct': questions_correct,
            'challenge_questions_quantity_shown': challenge_quantity,
            'challenge_questions_quantity_correct': challenge_correct,
            'received_soft_fail': _convert_bool_to_int(received_soft_fail),
            'received_hard_fail': _convert_bool_to_int(received_hard_fail),
            'approved_for_checkout': _convert_bool_to_int(approved_for_checkout)
        }
        if blocklist_id:
            payload['blocklist_id'] = int(blocklist_id)

        return self._post(url, json={'data': {'attributes': payload,
                                              'type': 'reservation-guest'}}, headers=headers).json()


def _trip_protection_to_integer(trip_protection: bool) -> int:
    """Convert from True/False/None to 1/0/-1"""
    if trip_protection is None:
        return 0
    return 1 if trip_protection else -1


def _convert_bool_to_int(value):
    """ Some connect API endpoints expect 1/0 instead of True/False.  They're also picky that null should be false """
    return 1 if value else 0


def _is_uuid4(value: str) -> bool:
    """ Check if a string looks like a valid UUID4 """
    try:
        uuid = UUID(value, version=4)
    except ValueError:
        return False

    return str(uuid) == value
