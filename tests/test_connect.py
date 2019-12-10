from copy import deepcopy
from unittest.mock import patch, ANY, MagicMock

import pendulum
import pytest

from vacasa.connect import VacasaConnect
from .test_data import TEST_DATA
from .test_expected import TEST_EXPECTED

fake_access_token = {
    'access_token': 'fake_access_token',
    'expires_at': pendulum.now().add(days=1).to_datetime_string()
}
fake_refresh_token = {
    'refresh_token': 'fake_refresh_token',
    'expires_at': pendulum.now().add(days=1).to_datetime_string()
}
mock_idp = MagicMock()


def mock_connect():
    connect = VacasaConnect(mock_idp, 'https://fake_url')

    # mock call that generates tokens
    mock_response = MagicMock()
    mock_response.return_value = None

    return connect


def test_add_meta_param_adds_one_to_empty():
    connect = mock_connect()
    params = {}
    params = connect._add_meta_param(params, 'include_photos')
    expected = {'include_meta': ',include_photos'}

    assert params == expected


def test_add_meta_param_adds_another_to_existing():
    connect = mock_connect()
    params = {'include_meta': ',include_photos'}
    params = connect._add_meta_param(params, 'amenities_map')
    expected = {'include_meta': ',include_photos,amenities_map'}

    assert params == expected


def test_ensure_https():
    with pytest.raises(ValueError) as e:
        VacasaConnect(mock_idp, 'http://fake_endpoint')

    assert str(e).endswith("`endpoint` scheme must be https")


# ----- Create Reservations Import ----- #
@patch.object(VacasaConnect, '_post')
def test_create_reservations_import(mock_post):
    connect = mock_connect()
    test_data = deepcopy(TEST_DATA['create_reservation_import'])
    connect.create_reservation_import(**test_data)
    constructed_dict = {k: v for k, v in test_data.items() if v is not None}
    mock_post.assert_called_once_with('https://fake_url/v1/reservations-import',
                                      headers=ANY,
                                      json=dict(data=dict(attributes=deepcopy(constructed_dict))))


# ----- Create Reservation ----- #
@patch.object(VacasaConnect, '_post')
def test_create_reservation_passes_terms(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_with_terms']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_with_terms']))


@patch.object(VacasaConnect, '_post')
def test_create_reservation_ignores_missing_terms(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_without_terms']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_without_terms']))


@patch.object(VacasaConnect, '_post')
def test_create_reservation_passes_booked_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_with_booked_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_with_booked_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_reservation_ignores_missing_booked_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_without_booked_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_without_booked_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_reservation_passes_display_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_with_display_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_with_display_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_reservation_ignores_missing_display_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_without_display_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_without_display_currency_code']))


# ----- Create Cancelled Reservation ----- #
@patch.object(VacasaConnect, '_post')
def test_create_cancelled_reservation_passes_booked_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_with_booked_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_with_booked_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_cancelled_reservation_ignores_missing_booked_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_without_booked_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_without_booked_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_cancelled_reservation_passes_display_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_with_display_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_with_display_currency_code']))


@patch.object(VacasaConnect, '_post')
def test_create_cancelled_reservation_ignores_missing_display_currency_code(mock_post):
    connect = mock_connect()

    connect.create_reservation(**deepcopy(TEST_DATA['reservation_without_display_currency_code']))
    mock_post.assert_called_once_with('https://fake_url/v1/reservations',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['reservation_without_display_currency_code']))


# ----- Contracts (DOCUMENTS) ----- #
@patch.object(VacasaConnect, '_post')
def test_create_contract(mock_post):
    connect = mock_connect()

    connect.create_contract(**deepcopy(TEST_DATA['normal_contract']))
    mock_post.assert_called_once_with('https://fake_url/v1/contracts',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['normal_contract']))


# ----- Contacts (PEOPLE) ----- #
@patch.object(VacasaConnect, '_post')
def test_create_contact(mock_post):
    connect = mock_connect()

    connect.create_contact(**deepcopy(TEST_DATA['normal_contact']))
    mock_post.assert_called_once_with('https://fake_url/v1/contacts',
                                      headers=ANY,
                                      json=deepcopy(TEST_EXPECTED['normal_contact']))


@patch.object(VacasaConnect, '_patch')
def test_update_finance_payload(mock_patch):
    connect = mock_connect()

    connect.update_contact_finances_payload(12345, deepcopy(TEST_DATA['normal_contact_finances']))
    mock_patch.assert_called_once_with('https://fake_url/v1/contacts/12345/finances',
                                       headers=ANY,
                                       json=deepcopy(TEST_EXPECTED['normal_contact_finances']))


@patch.object(VacasaConnect, '_patch')
def test_update_finance(mock_patch):
    connect = mock_connect()

    connect.update_contact_finances(12340, **deepcopy(TEST_DATA['normal_contact_finances']))
    mock_patch.assert_called_once_with('https://fake_url/v1/contacts/12340/finances',
                                       headers=ANY,
                                       json=deepcopy(TEST_EXPECTED['normal_contact_finances']))
