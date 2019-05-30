from copy import deepcopy

TEST_DATA = dict(
    reservation_without_terms=dict(
        unit_id=1,
        arrival='2020-01-01',
        departure='2020-01-31',
        email='test@vacasa.com',
        address='123 Main St',
        adults=4,
        quote_id='foo',
        first_name='Jane',
        last_name='Doe',
        account_number='bar',
        exp_mmyy='0130'
    )
)

# terms
TEST_DATA['reservation_with_terms'] = deepcopy(TEST_DATA['reservation_without_terms'])
TEST_DATA['reservation_with_terms']['terms'] = '2019-04-30T16:00:00Z'


# booked_currency_code
TEST_DATA['reservation_with_booked_currency_code'] = deepcopy(TEST_DATA['reservation_without_terms'])
TEST_DATA['reservation_with_booked_currency_code']['booked_currency_code'] = 'CLP'
TEST_DATA['reservation_without_booked_currency_code'] = deepcopy(TEST_DATA['reservation_without_terms'])

# display_currency_code
TEST_DATA['reservation_with_display_currency_code'] = deepcopy(TEST_DATA['reservation_without_terms'])
TEST_DATA['reservation_with_display_currency_code']['display_currency_code'] = 'CLP'
TEST_DATA['reservation_without_display_currency_code'] = deepcopy(TEST_DATA['reservation_without_terms'])
