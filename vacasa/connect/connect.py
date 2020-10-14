"""Vacasa Connect Python SDK."""
import logging
from urllib.parse import urlparse, urlunparse
from uuid import UUID

from requests import HTTPError

from .idp_auth import IdpAuth
from .requests_config import request_with_retries
from .util import log_http_error, is_https_url, subtract_days

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

    @staticmethod
    def _patch(url, data: dict = None, json: dict = None, headers: dict = None):
        """HTTP PATCH request helper."""
        if not headers:
            headers = {}
        r = requests.patch(url, data=data, json=json, headers=headers)
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

    def update_unit(self, unit_id, params: dict = None, amenities_map: dict = None):
        """
        Update a unit via connect.
        https://vacasa.docs.stoplight.io/reference/v1-units-id/update-unit

        Args:
            unit_id: ID of the unit to update
            params: A dict of key value pairs to update.
            amenities_map: Map of beds to update

        Returns: dict
             updated unit

        """
        if params is None and amenities_map is None:
            return "Invalid update parameters"

        payload = {}

        url = f"{self.endpoint}/v1/units/{unit_id}"

        if params is not None:
            payload['attributes'] = params

        if amenities_map is not None:
            payload['meta'] = {'amenities_map': amenities_map}

        return self._patch(url, json={'data': payload},
                           headers=self._headers()).json()

    def create_unit(self,
                    housing_type: str,
                    secured_by,
                    turnover_day: int = 0,
                    code: str = None,
                    name: str = None,
                    bedrooms: int = 0,
                    full_baths: int = 0,
                    half_baths: int = 0,
                    max_occupancy: int = 0,
                    latitude: int = 0,
                    longitude: int = 0,
                    amenity_email: str = '',
                    m_source: str = '',
                    address: dict = None,
                    king_beds: int = 0,
                    queen_beds: int = 0,
                    double_beds: int = 0,
                    twin_beds: int = 0,
                    sofabed: int = 0,
                    futon: int = 0
                    ):
        """
        Create a unit via connect. Required args are at the top of the list.
            https://vacasa.docs.stoplight.io/units/postv1units

        Args:
            housing_type: Effective foreign key to table Codes with CodeTypeId = 2,
                          corresponds to “Housing Type” on Listing tab for a unit
            secured_by: An int id of a user/process that signed up the unit
            turnover_day: Corresponds to “Fixed Turnover” on Rates tab for a unit
            code: Unit code, alternate unique identifier for a unit.
                  If not provided the Connect API will assign a temp code
            name: Unique name for the unit. Can be empty
            bedrooms:
            full_baths:
            half_baths:
            max_occupancy:
            latitude:
            longitude:
            amenity_email: Selected from hardcoded list of email addresses in Admin source code,
                           corresponds to “Send Amenity Request Email to” on Listing tab for a unit
            m_source: Effective foreign key to table Codes with CodeTypeId = 3,
                      corresponds to “Source” on Listing tab for a unit,
            address:
            king_beds:
            queen_beds:
            double_beds:
            twin_beds:
            sofabed:
            futon:

        Returns: dict
            Created unit with additional calculated fields
        """

        url = f"{self.endpoint}/v1/units"
        headers = self._headers()

        payload = {
            "housing_type": housing_type,
            "bedrooms": bedrooms,
            "bathrooms": {
                "full_baths": full_baths,
                "half_baths": half_baths,
            },
            "max_occupancy": max_occupancy,
            "turnover_day": turnover_day,
            "latitude": latitude,
            "longitude": longitude,
            "amenity_email": amenity_email,
            "m_source": m_source,
            "address": {} if address is None else address,
            "secured_by": secured_by,
        }

        if code:
            payload["code"] = code
        if name:
            payload["name"] = name

        amenities_map = {
            "KingBeds": king_beds,
            "QueenBeds": queen_beds,
            "DoubleBeds": double_beds,
            "TwinBeds": twin_beds,
            "Sofabed": sofabed,
            "Futon": futon
        }

        return self._post(url,
                          json={'data': {'attributes': payload, 'meta': {'amenities_map': amenities_map}}},
                          headers=headers
                          ).json()

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

    def add_unit_amenity(self,
                         amenity_id: int,
                         unit_id: int,
                         amenity_value: int = None,
                         internal_notes: str = None,
                         instructions: str = None,
                         notes: str = None,
                         provider_id: int = None) -> dict:
        """Add a new unit amenity in Connect.

        Args:
            amenity_id: An amenity ID.
            unit_id: A unit ID.
            amenity_value: An amenity value.
            internal_notes: An internal note.
            instructions: An instruction.
            notes: A note.
            provider_id: A provider ID.

        Returns:
            json response for success
        """
        url = f"{self.endpoint}/v1/unit-amenities"
        headers = self._headers()
        payload = {
            'data': {
                'type': 'unit-amenities',
                'attributes': {
                    'amenity_id': amenity_id,
                    'unit_id': unit_id,
                    'amenity_value': amenity_value,
                    'internal_notes': internal_notes,
                    'instructions': instructions,
                    'notes': notes,
                    'provider_id': provider_id,
                }
            }
        }

        r = self._post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    def update_unit_amenity(self, unit_amenity_id, params: dict):
        """Update a unit amenity in Connect.

        Args:
             unit_amenity_id: ID of the Unit Amenity to update.
             params: A dict of key value pairs to update.

        Yields:
            An updated unit amenity.
        """
        url = f"{self.endpoint}/v1/unit-amenities/{unit_amenity_id}"
        headers = self._headers()
        payload = {
            'data': {
                'type': 'unit-amenities',
                'attributes': params
            }
        }

        r = self._patch(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    def get_unit_amenity_properties(self, params: dict = None):
        """Retrieve a list of all unit amenity properties

        Yields:
            An iterator of unit amenity properties. Each unit amenity property is a dict.
        """
        url = f"{self.endpoint}/v1/unit-amenity-properties"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def add_unit_amenity_property(self,
                                  amenity_id: int,
                                  unit_id: int,
                                  idamenities_properties: int,
                                  property_value: str) -> dict:
        """Add a new unit amenity property in Connect.

        Args:
            amenity_id: An amenity ID.
            unit_id: A unit ID.
            idamenities_properties: An amenity property ID.
            property_value: The property value for the new unit amenity property.

        Returns:
            json response for success
        """
        url = f"{self.endpoint}/v1/unit-amenity-properties"
        headers = self._headers()
        payload = {
            'data': {
                'type': 'unit-amenity-property',
                'attributes': {
                    'amenity_id': amenity_id,
                    'unit_id': unit_id,
                    'idamenities_properties': idamenities_properties,
                    'property_value': property_value
                }
            }
        }

        r = self._post(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

    def update_unit_amenity_property(self, unit_amenity_property_id, params: dict):
        """Update a unit amenity property in Connect.

        Args:
             unit_amenity_property_id: ID of the Unit Amenity Property to update.
             params: A dict of key value pairs to update.

        Yields:
            An updated unit amenity property.
        """

        url = f"{self.endpoint}/v1/unit-amenity-properties/{unit_amenity_property_id}"
        headers = self._headers()
        payload = {
            'data': {
                'type': 'unit-amenity-property',
                'attributes': params
            }
        }

        r = self._patch(url, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()

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

    def get_reservation_by_id(self, reservation_id):
        """ Get a single reservation by ID """
        if not reservation_id:
            return None
        url = f"{self.endpoint}/v1/reservations/{reservation_id}"
        try:
            return self._get(url, headers=self._headers()).json()['data']
        except (HTTPError, KeyError):
            return None

    def get_reservation_by_confirmation_code(self, confirmation_code):
        """ Get a single reservation by confirmation code """
        if not confirmation_code:
            return None
        try:
            result_list = self.get_reservations(params={'filter[confirmation_code]': confirmation_code})
            return next(result_list, None)
        except (HTTPError, KeyError):
            return None

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

        Returns:
            The response object as a dict
        """
        url = f"{self.endpoint}/v2/quotes"
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
                           terms: str = None,
                           booked_currency_code: str = None,
                           display_currency_code: str = None,
                           fsc: list = None,
                           headers: dict = None
                           ) -> dict:
        """ Reserve a given unit

        Args:
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
            booked_currency_code: The currency of record for the unit being
                booked in ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            display_currency_code: The currency preference of the guest in
                ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            fsc: A list of credit dicts. Each credit object should contain
                credit_account_id, email, and amount fields.
            headers: custom headers to be passed in and added to the dictionary
                of common headers created by the _headers() method

        Returns:
            A response object as a dict
        """
        url = f"{self.endpoint}/v1/reservations"
        if headers:
            headers.update(self._headers())
        else:
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

        if fsc:
            payload['fsc'] = fsc

        if initial_payment_amount:
            payload['initial_payment_amount'] = initial_payment_amount

        if anonymous_id is not None:
            if _is_uuid4(anonymous_id):
                payload['anonymous_id'] = anonymous_id
            elif not anonymous_id.startswith('vacasa-qa-'):
                logger.info("Ignoring invalid UUID4: %s", anonymous_id)

        if terms is not None:
            payload['terms'] = terms

        if booked_currency_code is not None:
            payload['booked_currency_code'] = booked_currency_code

        if display_currency_code is not None:
            payload['display_currency_code'] = display_currency_code

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
                                     cancellation_reason: str = None,
                                     booked_currency_code: str = None,
                                     display_currency_code: str = None
                                     ) -> dict:
        """Cancel a reservation

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
            cancellation_reason: The reason that the reservation is being
                cancelled (e.g. 'Cart Abandoned').
            booked_currency_code: The currency of record for the unit being
                booked in ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            display_currency_code: The currency preference of the guest in
                ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).

        Returns:
            A response object as a dict
        """

        url = f"{self.endpoint}/v1/reservations-abandoned"
        headers = self._headers()
        last_night = subtract_days(departure, 1)
        if last_night is None:
            raise ValueError("Invalid departure date", departure)

        payload = {
            'adults': adults,
            'first_night': arrival,
            'children': children,
            'email': email,
            'cleaning_fees': cleaning_fees,
            'last_night': last_night,
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

        if booked_currency_code is not None:
            payload['booked_currency_code'] = booked_currency_code

        if display_currency_code is not None:
            payload['display_currency_code'] = display_currency_code

        if anonymous_id is not None:
            if _is_uuid4(anonymous_id):
                payload['anonymous_id'] = anonymous_id
            else:
                logger.warning("Ignoring invalid UUID4: %s", anonymous_id)

        return self._post(url, json={'data': {'attributes': payload}}, headers=headers).json()

    def create_reservation_import(self,
                                  adults: int,
                                  arrival: str,
                                  departure: str,
                                  first_name: str,
                                  last_name: str,
                                  unit_id: int,
                                  address: dict = None,
                                  anonymous_id: str = None,
                                  autopay: int = None,
                                  booked_currency_code: str = None,
                                  children: int = 0,
                                  clean_after_stay: int = None,
                                  created_by: int = None,
                                  currency_code: str = None,
                                  display_currency_code: str = None,
                                  email: str = None,
                                  listing_channel_reservation_id: str = None,
                                  fees: list = None,
                                  notes: list = None,
                                  paid: int = None,
                                  pets: int = 0,
                                  phone: str = None,
                                  phone2: str = None,
                                  rent: list = None,
                                  source: str = None,
                                  taxes: list = None,
                                  total: int = None,
                                  trip_protection: bool = None,
                                  type: int = None,
                                  ):
        """

        Args:
            adults: How many adults will be staying
            arrival: Checkin date in 'YYYY-MM-DD' format
            departure: Checkout date in 'YYYY-MM-DD' format
            first_name: User's First Name (for billing)
            last_name: User's Last Name (for billing)
            unit_id: A Vacasa Unit ID
            address: User's address information, e.g.
                    {
                    'address_1': '999 W Main St #301',
                    'city': 'Boise',
                    'state': 'ID',
                    'zip': '83702'
                    }
            anonymous_id (optional): UUID4 for tracking,
            autopay: A flag to determine auto pay
                        1 = Yes,
                        0 = No,
                        -1 = Special
            booked_currency_code: The currency of record for the unit being
                    booked in ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            children: How many children will be staying
            clean_after_stay: A flag to determine if a unit should be cleaned after a stay
                        1 = Yes,
                        0 = No
            created_by: User ID from logins.UserID that gets written to Reservations.CreateBy.
                    For non-zero values, this is the Acquisition Rep's UserID
            currency_code: ISO-4217 currency code
            display_currency_code: The currency preference of the guest in
                    ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            email: User's email address
            listing_channel_reservation_id: Enter the original reservation ID from the acquired company
            fees: A list of fees by ID and amount
                [{
                    'id': int,
                    'amount': float
                }]
            notes: Use this field to provide miscellaneous information about reservation
            paid: The total amount paid thus far. Paid amount may not exceed total.
            pets: How many pets will be staying
            phone: User's phone number
            phone2: User's secondary phone number
            rent: List of rent by day. Fields used here are date, amount, and ltd.
                  See Folio API docs for more information
                [{
                    'date': string,
                    'rent': float
                    'ltd': float
                }]
            source: A Vacasa-issued code identifying the source of this request
            taxes: List of taxes by id and amount
                [{
                    'id': int,
                    'amount': float
                }]
            total: The total amount of the reservation (Fees + Taxes + Rent)
            trip_protection: Has the user requested trip protection?
                    False: No
                    None: TBD
                    True: Yes
            type: The type of reservation to be created
                    3 = Vacasa Hold,
                    2 = Owner Hold,
                    1 = Reservation

        Returns:
            A response as a dict
        """
        optional_parameters = {'address': address,
                               'anonymous_id': anonymous_id,
                               'autopay': autopay,
                               'booked_currency_code': booked_currency_code,
                               'children': children,
                               'clean_after_stay': clean_after_stay,
                               'created_by': created_by,
                               'currency_code': currency_code,
                               'display_currency_code': display_currency_code,
                               'email': email,
                               'listing_channel_reservation_id': listing_channel_reservation_id,
                               'fees': fees,
                               'notes': notes,
                               'paid': paid,
                               'pets': pets,
                               'phone': phone,
                               'phone2': phone2,
                               'rent': rent,
                               'source': source,
                               'taxes': taxes,
                               'total': total,
                               'trip_protection': trip_protection,
                               'type': type
                               }

        url = f"{self.endpoint}/v1/reservations-import"
        headers = self._headers()
        payload = {
            'adults': adults,
            'arrival': arrival,
            'departure': departure,
            'first_name': first_name,
            'last_name': last_name,
            'unit_id': unit_id
        }
        payload.update({k: v for k, v in optional_parameters.items() if v is not None})
        return self._post(url, json={'data': {'attributes': payload}}, headers=headers).json()

    def create_reservation_seed(self,
                                booked_currency_code: str,
                                quote_id: str,
                                created_by: int,
                                source: str = None,
                                anonymous_id: str = None):
        """

        Args:
            booked_currency_code: The currency of record for the unit being
                booked in ISO 4217 alpha code format (e.g. 'USD', 'CLP', etc.).
            quote_id: ID of a quote retrieved from the `GET /quotes` endpoint
            created_by: The user_id of the user creating the reservation
            source: A Vacasa-issued code identifying the source of this request
            anonymous_id (optional): UUID4 for tracking

        Returns:
            A response object as a dict
        """
        url = f"{self.endpoint}/v1/reservations-seed"
        headers = self._headers()
        payload = dict(
            booked_currency_code=booked_currency_code,
            quote_id=quote_id,
            created_by=created_by
        )

        if source is not None:
            payload['source'] = source

        if anonymous_id:
            payload['anonymous_id'] = anonymous_id

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

        Returns:
            e.g.: {'result': 'success', 'id': 8411, 'meta': {'transaction_id': '5c393085ecd86'}}
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

        Returns:
            The response object as a dict
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
        """Add a new guest to an existing reservation

        Args:
            reservation_id: A reservation identifier.
            first_name: The first name of the guest being added.
            last_name: The last name of the guest being added.
            email: The email address of the guest being added.

        Returns:
            json response for success
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
                           questions_quantity: int = 0,
                           questions_correct: int = 0,
                           challenge_quantity: int = 0,
                           challenge_correct: int = 0,
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

    def get_contracts(self,
                      params: dict = None,
                      active_only: bool = True):
        """
        https://vacasa.docs.stoplight.io/contracts/get-contracts-list
        Args:
            params: Params used to filter query.
            active_only: Show only the active contracts

        Yields:
            An iterator of contracts
        """

        if params is None:
            params = {}

        if not active_only:
            params['filter[terminated]'] = False

        url = f"{self.endpoint}/v1/contracts"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def create_contract(self,
                        unit_id: int,
                        management_fee: float,
                        owners: list,
                        created_by: int,
                        start_date: str,
                        end_date: str = '2099-01-01',
                        monthly_rent: float = 0,
                        template_version_id: int = 1,
                        form_id: int = 1,
                        channel_fee_cost_sharing_id: int = 5,
                        amendment_by_notice_id: int = 4,
                        referral_eligible: bool = False,
                        referral_discount: int = 0):
        """
        https://vacasa.docs.stoplight.io/contracts/postv1contracts
        Args:
            unit_id:  Id of the unit associated with the contract
            management_fee: Number representing the percentage that Vacasa gets on a rental
            owners: List of objects that contain three properties 'percentage_ownership', 'tax_ownership', 'contact_id'
            created_by: ID of logged in user
            start_date: Start date of the contract
            end_date: End date of a contract (By default will be '2099-01-01'
            monthly_rent: Fixed monthly rent per contract
            template_version_id: Foreign key to table contract_template_version,
                                 corresponds to “Template Version” on Contract page in Admin
            form_id: Foreign key to table contract_form, corresponds to “Contract Form” on Contract page in Admin
            channel_fee_cost_sharing_id: Foreign key to table contract_channel_fee_cost_sharing,
                                         corresponds to “Channel Fee Cost Sharing” on Contract page in Admin
            amendment_by_notice_id: Foreign key to table contract_amendment_by_notice,
                                    corresponds to “Amendment by Notice” on Contract page in Admin
            referral_eligible: Corresponds to “Owner Referral Eligible” on Contract page in Admin
            referral_discount: Corresponds to “Owner Referral Discount” on Contract page in Admin

        Returns: dict
            Created Contract
        """

        payload = {
            "unit_id": unit_id,
            "management_fee": management_fee,
            "monthly_rent": monthly_rent,
            "start_date": start_date,
            "end_date": end_date,
            "template_version_id": template_version_id,
            "form_id": form_id,
            "channel_fee_cost_sharing_id": channel_fee_cost_sharing_id,
            "amendment_by_notice_id": amendment_by_notice_id,
            "owners": owners,
            "referral_eligible": referral_eligible,
            "referral_discount": referral_discount,
            "created_by": created_by
        }

        url = f"{self.endpoint}/v1/contracts"
        headers = self._headers()

        return self._post(url,
                          json={'data': {'attributes': payload}},
                          headers=headers
                          ).json()

    def get_contract_template_versions(self):
        """
        Yields:
            Iterator of contract template versions, each one is a dict
        """

        params = {}
        url = f"{self.endpoint}/v1/contract-template-versions"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_contract_forms(self):
        """
        Yields:
            Iterator of contract forms, each one is a dict
        """

        params = {}
        url = f"{self.endpoint}/v1/contract-forms"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_contract_channel_fee_cost_sharings(self):
        """
        Yields:
            Iterator of contract channel fee cost sharings, each one is a dict
        """

        params = {}
        url = f"{self.endpoint}/v1/contract-channel-fee-cost-sharings"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_contract_amendment_by_notices(self):
        """
        Yields:
            Iterator of contract amendment by notices, each one is a dict
        """

        params = {}
        url = f"{self.endpoint}/v1/contract-amendment-by-notices"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_contacts(self,
                     params: dict = None):
        """
        https://vacasa.docs.stoplight.io/contacts/getv1contacts

        Args:
            params: Filters to reduce set of contacts

        Yields:
            Iterator of contacts, each contact is a dict
        """

        if params is None:
            params = {}

        url = f"{self.endpoint}/v1/contacts"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_contact_languages(self):
        """
        Yields:
            Iterator of contact language preferences, each one is a dict
        """

        params = {}
        url = f"{self.endpoint}/v1/languages"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def create_contact(self,
                       first_name: str,
                       email: str,
                       language_id: int,
                       last_name: str = None,
                       address_1: str = None,
                       address_2: str = None,
                       city: str = None,
                       state: str = None,
                       zip: str = None,
                       country_code: str = None,
                       phone: str = None,
                       phone_notes: str = None,
                       created_by: int = None,
                       tax_entity_name: str = None,
                       send_email: bool = False
                       ):
        """
        https://connect.vacasa.com/#tag/Contacts/paths/~1v1~1contacts/post

        Args:
            first_name: First name of the contact
            email: Email of the contact
            last_name: Last name of contact
            address_1: Mailing address line 1 of contact
            address_2: Mailing address line 2 of contact
            city: Mailing city address of contact
            state: Mailing state of contact
            zip: Mailing zip code of contact
            country_code: Mailing country code of contact
            phone: Phone Number of contact
            phone_notes: Corresponds to “Phone Notes” on Contact page in Admin
            language_id: Foreign key to table languages
            created_by: ID of logged in user
            tax_entity_name: If the contact is a business, put the business name here
            send_email: Whether or not to send an email with account/login info

        Returns: dict
            Created Contact

        """
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "address_1": address_1,
            "address_2": address_2,
            "city": city,
            "state": state,
            "zip": zip,
            "country_code": country_code,
            "email": email,
            "phone": phone,
            "phone_notes": phone_notes,
            "language_id": language_id,
            "created_by": created_by,
            "tax_entity_name": tax_entity_name,
            "send_email": send_email,
        }

        #Using dict comprehension to remove items that are None

        payload = {k: v for k, v in payload.items() if v is not None}

        url = f"{self.endpoint}/v1/contacts"
        headers = self._headers()

        return self._post(url,
                          json={'data': {'attributes': payload}},
                          headers=headers
                          ).json()

    def update_contact(self, contact_id, params: dict):
        """
        Update a contact via connect.
        https://connect.vacasa.com/#tag/Contacts/paths/~1v1~1contacts/patch

        Args:
            contact_id: ID of the contact to update
            params: A dict of key value pairs to update.

        Returns: dict
             updated contact

        """

        url = f"{self.endpoint}/v1/contacts/{contact_id}"
        return self._patch(url, json={'data': {'attributes': params}}, headers=self._headers()).json()

    def update_contact_finances(self,
                                contact_id,
                                account_name: str = None,
                                account_number: str = None,
                                routing_number: str = None,
                                tax_id: str = None,
                                tax_entity_name: str = None,
                                tax_form_code_id: int = 0):
        """
        Update a contacts finances via connect.
        https://connect.vacasa.com/#tag/Contacts/paths/~1v1~1contacts~1{id}~1finances/patch

        Args:
            contact_id: ID of the contact to update
            account_name: Bank Account Name (<= 100 Chars)
            account_number: Bank Account Number (<= 25 Chars)
            routing_number: Bank Routing Number (<= 20 Chars)
            tax_id: Tax Identification (<= 11 Chars)
            tax_entity_name: Tax Name (<= 100 Chars)
            tax_form_code_id:


        Returns: None
             Sensitve data.. no result (HTTP-204)

        """
        self.update_contact_finances_payload(contact_id, dict(
            account_name=account_name,
            account_number=account_number,
            routing_number=routing_number,
            tax_id=tax_id,
            tax_entity_name=tax_entity_name,
            tax_form_code_id=tax_form_code_id))

    def update_contact_finances_payload(self, contact_id, params: dict):
        """
        Update a contacts finances via connect.
        https://connect.vacasa.com/#tag/Contacts/paths/~1v1~1contacts~1{id}~1finances/patch

        Args:
            contact_id: ID of the contact to update
            params: A dict of key value pairs to update.

        Returns: None
             Sensitve data.. no result (HTTP-204)

        """

        url = f"{self.endpoint}/v1/contacts/{contact_id}/finances"
        self._patch(url, json={'data': {'attributes': params}}, headers=self._headers())

    def get_language_list(self):
        """Get a list of languages from Connect"""
        url = f"{self.endpoint}/v1/languages"
        return self._get(url, headers=self._headers())

    def _preview_adjustment(self, reservation_id: str, user_id: int, policy_info: dict):
        """ Create a preview of the effects of applying an Adjustment Policy to a Reservation """
        path = f"{self.endpoint}/v1/reservation-adjustments/"

        payload = {
            'data': {
                'type': 'reservation-adjustment',
                'attributes': {
                    "adjustment_policy": {'policy_info': policy_info},
                    "reservation_id": reservation_id,
                    "user_id": user_id
                }
            }
        }

        return self._post(path, json=payload, headers=self._headers())

    def cancel_reservation_preview(self, reservation_id: str, user_id: int, force_zero: bool = False):
        """ Create a preview of the effects of cancelling a reservation """
        return self._preview_adjustment(reservation_id, user_id, policy_info={
            'policy_type': 'cancel-reservation',
            'force_zero': force_zero
        })

    def _apply_adjustment(self,
                          reservation_id: str,
                          user_id: int,
                          adjustment_uuid: str,
                          policy_info: dict = None):
        """Apply an Adjustment Policy to a Reservation"""
        path = f"{self.endpoint}/v1/booking/{reservation_id}/adjustment/{adjustment_uuid}"

        payload = {
            'data': {
                'type': 'reservation-adjustment',
                'attributes': {
                    "reservation_id": reservation_id,
                    "user_id": user_id
                }
            }
        }

        if policy_info:
            payload['data']['attributes']['adjustment_policy'] = {'policy_info': policy_info}

        return self._patch(path, json=payload, headers=self._headers())

    def cancel_reservation_apply(self,
                                 reservation_id: str,
                                 user_id: int,
                                 adjustment_uuid: str,
                                 fsc_rate: float = None,
                                 fsc_note: str = None,
                                 email: str = None):
        """ Cancel a reservation by applying an adjustment policy (requires a UUID from cancel_reservation_preview """
        policy_info = None

        if fsc_rate is not None:
            policy_info = {
                'fsc': {
                    "rate": fsc_rate,
                    "note": fsc_note
                }
            }

            if email:
                policy_info['fsc']['email'] = email

        return self._apply_adjustment(reservation_id, user_id, adjustment_uuid, policy_info)

    def get_unit_reservation_buffers(self, params: dict = None):
        """
        get a list of unit reservation buffers
        """

        url = f"{self.endpoint}/v1/unit-reservation-buffers"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_reservation_buffer_by_id(self, unit_reservation_buffer_id: int):
        """
        get an unit reservation buffer by id
        """

        url = f"{self.endpoint}/v1/unit-reservation-buffers/{unit_reservation_buffer_id}"
        headers = self._headers()

        return self._get(url, headers).json()

    def create_unit_reservation_buffer(self,
                                       unit_id: int,
                                       buffer_days: int,
                                       start_date: str,
                                       end_date: str,
                                       reason_id: int):
        """
        create a unit reservation buferr
        """

        payload = {
            'data': {
                'type': 'unit-reservation-buffer',
                'attributes': {
                    "unit_id": unit_id,
                    "buffer_days": buffer_days,
                    "start_date": start_date,
                    "end_date": end_date,
                    "unit_reservation_buffer_reason_id": reason_id
                }
            }
        }

        url = f"{self.endpoint}/v1/unit-reservation-buffers"
        headers = self._headers()

        return self._post(url, json=payload, headers=headers).json()

    def update_unit_reservation_buffer(self, unit_reservation_buffer_id: int, params: dict):
        """
        update a unit reservation buffer
        """

        url = f"{self.endpoint}/v1/unit-reservation-buffers/{unit_reservation_buffer_id}"
        headers = self._headers()

        attributes = {
            "unit_id": params["unit_id"],
            "buffer_days": params["buffer_days"],
            "start_date": params["start_date"],
            "end_date": params["end_date"],
            "unit_reservation_buffer_reason_id": params["reason_id"]
        }

        return self._patch(url, json={'data': {
            'type': 'unit-reservation-buffer', 'attributes': attributes}}, headers=headers).json()

    def get_unit_blocks(self, params: dict = None):
        """
        get a list of unit blocks
        """

        url = f"{self.endpoint}/v1/unit-blocks"
        headers = self._headers()

        return self._iterate_pages(url, headers, params)

    def get_unit_unit_block_by_id(self, unit_block_id: int):
        """
        get an unit block by id
        """

        url = f"{self.endpoint}/v1/unit-blocks/{unit_block_id}"
        headers = self._headers()

        return self._get(url, headers).json()

    def create_unit_block(self,
                          unit_id: int,
                          unit_block_type_id: int,
                          days_out: int,
                          note: str):
        """
        create an unit block

        Args:
            unit_id: The id of the unit the unit block will be created for.
            unit_block_type_id: The type of unit block that will be applied to this unit.
            days_out: the ammount of days this unit block will be applied for this unit.
            note: Standard procedure - The note must have the name of the person doing this upload and brief info about the reason for this upload. 

        Returns:
            Returns an object representing the object created on the database.
        """

        payload = {
            'data': {
                'type': 'unit-block',
                'attributes': {
                    "unit_id": unit_id,
                    "unit_block_type_id": unit_block_type_id,
                    "days_out": days_out,
                    "note": note
                }
            }
        }

        url = f"{self.endpoint}/v1/unit-blocks"
        headers = self._headers()

        return self._post(url, json=payload, headers=headers).json()

    def update_unit_block(self, unit_block_id: int, params: dict):
        """
        update a unit block
        """

        url = f"{self.endpoint}/v1/unit-blocks/{unit_block_id}"
        headers = self._headers()

        return self._patch(url, json={'data': {
            'type': 'unit-block', 'attributes': params}}, headers=headers).json()

    def get_logins(self, email: str):
        """ Get logins by email address. """
        url = f"{self.endpoint}/v1/logins"
        headers = self._headers()
        params = {
            'filter[email]': email
        }

        return self._iterate_pages(url, headers, params)


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
