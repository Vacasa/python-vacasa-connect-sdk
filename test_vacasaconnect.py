import mock
import pendulum
from vacasaconnect import VacasaConnect


class TestVacasaConnect(object):

    fake_access_token = {
        'access_token': 'fake_access_token',
        'expires_at': pendulum.now().add(days=1).to_datetime_string()
    }
    fake_refresh_token = {
        'refresh_token': 'fake_refresh_token',
        'expires_at': pendulum.now().add(days=1).to_datetime_string()
    }

    @mock.patch.object(VacasaConnect, '_populate_tokens')
    def mock_connect(self, mock_populate_tokens):
        connect = VacasaConnect('fake_url', 'fake_key', 'fake_secret')

        # mock call that generates tokens
        mock_response = mock.Mock()
        mock_response.return_value = None
        mock_populate_tokens.return_value = mock_response

        # populate fake tokens
        connect._access_token = self.fake_access_token
        connect._refresh_token = self.fake_refresh_token

        return connect

    def test_generate_signature(self):
        connect = self.mock_connect()
        timestamp = int(pendulum.create(2017, 1, 1, 0, 0).timestamp())
        signature = connect._generate_signature(timestamp)
        expected = '87446b676b79b6e493a6b852ec3c32faf579086bd12728178197ef278ec7abfc'

        assert signature == expected
