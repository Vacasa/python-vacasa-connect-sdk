from copy import deepcopy

TEST_EXPECTED = dict(
    reservation_without_terms=dict(
        data=dict(
            attributes=dict(
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
                exp_mmyy='0130',
                children=0,
                pets=0,
                trip_protection=0,
                phone=None,
                source=None
            )
        )
    )
)

# terms
TEST_EXPECTED['reservation_with_terms'] = deepcopy(TEST_EXPECTED['reservation_without_terms'])
TEST_EXPECTED['reservation_with_terms']['data']['attributes']['terms'] = '2019-04-30T16:00:00Z'


# booked_currency_code
TEST_EXPECTED['reservation_with_booked_currency_code'] = deepcopy(TEST_EXPECTED['reservation_without_terms'])
TEST_EXPECTED['reservation_with_booked_currency_code']['data']['attributes']['booked_currency_code'] = 'CLP'
TEST_EXPECTED['reservation_without_booked_currency_code'] = deepcopy(TEST_EXPECTED['reservation_without_terms'])

# display_currency_code
TEST_EXPECTED['reservation_with_display_currency_code'] = deepcopy(TEST_EXPECTED['reservation_without_terms'])
TEST_EXPECTED['reservation_with_display_currency_code']['data']['attributes']['display_currency_code'] = 'CLP'
TEST_EXPECTED['reservation_without_display_currency_code'] = deepcopy(TEST_EXPECTED['reservation_without_terms'])
