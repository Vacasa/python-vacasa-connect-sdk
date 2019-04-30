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
