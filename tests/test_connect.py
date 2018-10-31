from unittest.mock import patch, MagicMock

import pendulum
import pytest

from vacasa.connect import VacasaConnect

fake_access_token = {
    'access_token': 'fake_access_token',
    'expires_at': pendulum.now().add(days=1).to_datetime_string()
}
fake_refresh_token = {
    'refresh_token': 'fake_refresh_token',
    'expires_at': pendulum.now().add(days=1).to_datetime_string()
}


@patch.object(VacasaConnect, '_populate_tokens')
def mock_connect(mock_populate_tokens):
    connect = VacasaConnect('fake_key', 'fake_secret', 'https://fake_url')

    # mock call that generates tokens
    mock_response = MagicMock()
    mock_response.return_value = None
    mock_populate_tokens.return_value = mock_response

    # populate fake tokens
    connect._access_token = fake_access_token
    connect._refresh_token = fake_refresh_token

    return connect


def test_generate_signature():
    connect = mock_connect()
    timestamp = int(pendulum.datetime(2017, 1, 1, 0, 0).timestamp())
    signature = connect._generate_signature(timestamp)
    expected = '87446b676b79b6e493a6b852ec3c32faf579086bd12728178197ef278ec7abfc'

    assert signature == expected


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
    with pytest.raises(ValueError):
        VacasaConnect('fake_key', 'fake_secret', 'http://fake_endpoint')
