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
        exp_mmyy='0130',
        headers={
            'X-Header': True
        }
    ),
    create_reservation_import=dict(
        adults=1,
        arrival='6/3/1949',
        departure='6/4/1949',
        first_name='George',
        last_name='Orwell',
        unit_id=1984,
        address=None,
        anonymous_id=None,
        autopay=None,
        booked_currency_code=None,
        children=3,
        clean_after_stay=None,
        created_by=None,
        currency_code=None,
        display_currency_code=None,
        email='big_brother@1984go.watching',
        fees=None,
        notes=None,
        paid=None,
        pets=None,
        phone=None,
        phone2=None,
        rent=None,
        source=None,
        taxes=None,
        total=None,
        trip_protection=None,
        type=None,
    ),
    normal_contact=dict(
        address_1="123 Main st",
        address_2="",
        city="Springfield",
        country_code="US",
        created_by=0,
        email="user@example.com",
        first_name="User",
        language_id=0,
        last_name="Namesson",
        phone="208-555-6677",
        phone_notes="Don't ever call after midnight",
        state="MO",
        tax_entity_name="Arbys",
        zip="string"
    ),
    normal_contract=dict(
        amendment_by_notice_id=4,
        channel_fee_cost_sharing_id=5,
        created_by=0,
        end_date="2019-08-15",
        form_id=1,
        management_fee=0,
        monthly_rent=0,
        owners=[
            dict(
                percentage_ownership=100,
                tax_ownership=100,
                contact_id=12345
            )
        ],
        referral_discount=0,
        referral_eligible=False,
        start_date="2019-08-15",
        template_version_id=1,
        unit_id=0
    ),
    normal_contact_finances=dict(
        account_name="Chemical Bank",
        account_number="987654321",
        routing_number="123456789",
        tax_id="00-0000-0",
        tax_entity_name="Arbys",
        tax_form_code_id=12
    ),
    ticket_data=dict(
        title="ticket title",
        unit_id=1,
        assigned_to=24351,
        severity=1,
        created_by=24351,
        display_severity="Urgent",
        display_status="Accepted",
        status=1
    ),
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
