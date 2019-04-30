TEST_DATA = dict(
    reservation_with_terms=dict(
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
        terms='2019-04-30T16:00:00Z'
    ),
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
