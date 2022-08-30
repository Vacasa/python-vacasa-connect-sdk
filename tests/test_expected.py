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
    ),
    normal_contact=dict(
        data=dict(
            attributes=dict(
                address_1= "123 Main st",
                address_2= "",
                city= "Springfield",
                country_code= "US",
                created_by= 0,
                email= "user@example.com",
                first_name= "User",
                language_id= 0,
                last_name= "Namesson",
                phone= "208-555-6677",
                phone_notes= "Don't ever call after midnight",
                state= "MO",
                tax_entity_name= "Arbys",
                zip= "string",
                send_email=False
            )
        )
    ),
    normal_contract=dict(
        data=dict(
            attributes=dict(
                amendment_by_notice_id= 4,
                channel_fee_cost_sharing_id= 5,
                created_by= 0,
                end_date= "2019-08-15",
                form_id= 1,
                management_fee= 0,
                monthly_rent= 0,
                owners= [
                    dict(
                        percentage_ownership= 100,
                        tax_ownership= 100,
                        contact_id= 12345
                        )
                    ],
                referral_discount= 0,
                referral_eligible= False,
                start_date= "2019-08-15",
                template_version_id= 1,
                unit_id= 0
            )
        )
    ),
    normal_contact_finances=dict(
        data=dict(
            attributes=dict(
                account_name= "Chemical Bank",
                account_number= "987654321",
                routing_number= "123456789",
                tax_id= "00-0000-0",
                tax_entity_name= "Arbys",
                tax_form_code_id= 12
            )
        )
    ),
    ticket_data=dict(
            type = 'ticket',
            attributes=dict(
                title="ticket title",
                unit_id=1,
                assigned_to=24351,
                severity=1,
                created_by=24351,
                display_severity="Urgent",
                display_status="Accepted",
                status=1
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
