# CHANGELOG

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.30.0] - 2024-03-21

### Changed
- Implemented singleton pattern for requests object in both `VacasaConnect` and `IdpAuth` classes
- Added connection pool configuration parameters:
  - `pool_connections`: Number of connection pools to maintain (one per host)
  - `pool_maxsize`: Maximum number of simultaneous connections per host
- Updated documentation to reflect new connection pool configuration options

## [4.29.0] - 2023-09-20

## Changed

-  Added call for expense debit methods

## [4.28.0] - 2023-03-17

## Changed

-  Added `create_ticket_comment` to allow posting ticket Comments through Connect

## [4.27.3] - 2023-02-24

## Changed

- Update get tickets to easily include comments

## [4.27.2] - 2023-02-02

## Changed

- Updated cryptography version range to be ==38.0.*

## [4.27.1] - 2023-02-02

## Changed

- Made cryptography version range in extras_require more explicit to attempt to resolve a setup command error

## [4.27.0] - 2022-09-07

## Changed

- Added `user_agent` argument to specify `User-Agent` value in request header.

## [4.26.0] - 2022-08-24

## Changed

- Added `update_ticket` and `create_ticket` to support `/v1/tickets` functionality.

## [4.25.0] - 2022-08-01

## Changed

- Added `get_tickets` and `get_ticket_by_id` to support `/v1/tickets` functionality.

## [4.24.0] - 2022-07-07

## Changed

- Added `required` filter to `get_amenities()`.

## [4.23.0] - 2021-01-03

## Changed

- Added `notes` parameter to `create_unit_reservation_buffer()`.

## [4.22.0] - 2021-09-07

## Changed

- Added `get_unit_bulk` to support `/v1/unit-bulk` functionality.

## [4.21.4] - 2021-09-07

## Changed

- Updated the python dependencies in response to Dependabot alerts.

## [4.21.3] - 2021-08-05

## Changed

- Updated the `install_requires` section of `setup.py` to match current version in the `Pipfile.lock`.

## [4.21.2] - 2021-07-23

## Added

- Added `get_acquisitions` to support `/v1/acquisitions` functionality

## [4.21.1] - 2020-12-17

## Changed

- Modified `create_contract` to only set `secured_by` if not `None`.

## [4.21.0] - 2020-12-16

## Changed

- Added `discount_id` parameter to `create_reservation_seed_from_finances()`.

## [4.20.0] - 2020-12-07

## Changed

- Added `secured_by` parameter to `create_contract`.

## [4.19.0] - 2020-12-07

## Added

- Added `create_reservation_seed_from_finances()` to support new `/v1/reservations-seed` functionality

## [4.18.0] - 2020-12-02

## Changed

- Modified `update_contact_finances()` to accept new parameters for changing W9 fields.

## [4.17.1] - 2020-11-25

## Changed

- Fixed accounting entity method params.

## [4.17.0] - 2020-11-25

## Changed

- Added GET, POST and PATCH methods for accounting entity units table.

## [4.16.0] - 2020-11-03

## Changed

- Added Delete method for unit reservation buffers.

## [4.15.0] - 2020-10-23

## Changed

- Modified `update_amentities()` and `update_amenity_properties()` to follow correct PATCH functionality and not send items to be updated that are null.

## [4.14.0] - 2020-10-14

## Added

- The `get_logins()` method, which uses [/v1/logins](https://connect.vacasa.com/#operation/get-logins-list)

## [4.13.3] - 2020-08-24

## Changed

- Changed how contact records are sent, only send fields that have data

## [4.13.2] - 2020-08-21

## Changed

- Fixing tab spacing issue

## [4.13.1] - 2020-08-21

## Changed

- Changed PATCH Unit to remove amenities map if not specified.

## [4.13.0] - 2020-07-24

### Changed

- Migrate from distutils -> setuptools

## [4.12.2] - 2020-07-21

### Added

- Add reason_id : `fix update_unit_reservation_buffer`

## [4.12.1] - 2020-07-20

### Added

- Add reason_id : `fix reason name field`

## [4.12.0] - 2020-07-20

### Added

- Add reason_id : `create_unit_reservation_buffer`

## [4.11.1] - 2020-07-16

### Added

- Fixed parameters for unit block creation: `get_unit_blocks`,`get_unit_unit_block_by_id`,`create_unit_block`,`update_unit_block`

## [4.11.0] - 2020-07-15

### Added

- Fixed identation for unit block endpoints: `get_unit_blocks`,`get_unit_unit_block_by_id`,`create_unit_block`,`update_unit_block`

## [4.10.0] - 2020-06-30

### Added

- Added endpoints for unit blocks management: `get_unit_blocks`,`get_unit_unit_block_by_id`,`create_unit_block`,`update_unit_block`

## [4.9.0] - 2020-06-26

### Added

- Added `fix reservation buffers methods`

## [4.8.0] - 2020-06-26

### Added

- Added `get_reservation_buffers`

## [4.7.0] - 2020-05-20

### Added

- Added `get_reservation_by_id()` and `get_reservation_by_confirmation_code()`

## [4.6.0] - 2020-05-20

### Added

- Added `cancel_reservation_preview()` and `cancel_reservation_apply()` to facilitate reservation cancelling, optionally
  issuing FSCs

## [4.5.0] - 2020-04-27

### Changed

- The `create_reservation()` method now accepts a list of credits to redeem as the new `fsc` parameter. This parameter
  is optional.

## [4.4.3] - 2020-02-14

### Changed

- Allow caller to use `leeway` to refresh token from IdpAuth before it expires.

## [4.4.2] - 2020-02-13

### Changed

- Update `add_unit_amenity_property` request parameter to `idamenities_properties`.

## [4.4.1] - 2020-01-30

### Changed

- Add type `unit-amenities` to add_unit_amenity and update_unit_amenity methods.

## [4.4.0] - 2020-01-27

### Added

- The `add_unit_amenity()` method, which uses [/v1/unit-amenities](https://connect.vacasa.com/#operation/post-unit-amenities)
- The `update_unit_amenity()` method, which uses [/v1/unit-amenities/{id}](https://connect.vacasa.com/#operation/patch-unit-amenities)

## [4.3.0] - 2020-01-27

### Added

- The `add_unit_amenity_property()` method, which uses [v1/unit-amenity-properties](https://connect.vacasa.com/#operation/create-unit-amenity-properties)
- The `update_unit_amenity_property()` method, which uses [/v1/unit-amenity-properties/{id}](https://connect.vacasa.com/#operation/update-unit-amenity-properties)

## [4.2.0] - 2020-01-27

### Added

- The `get_unit_amenity_properties()` method, which uses [v1/unit-amenity-properties](https://connect.vacasa.com/#operation/get-unit-amenity-properties)

## [4.1.0] - 2020-01-20

### Added

- param `headers` to the `create_reservation` method, which uses [v1/reservations](https://connect.vacasa.com/#operation/post-reservations)

## [4.0.5] - 2020-01-17

### Added

- Add call for contact languages.

## [4.0.4] - 2020-01-13

### Added

- Add calls for contract template versions, forms, channel fee cost sharings, and amendment by notices.

## [4.0.3] - 2020-01-07

### Changed

- 400 errors now logged as info, and only 500 errors added as errors.

## [4.0.1] - 2020-01-02

### Fixed

- create_cancelled_reservation() now properly converts the `departure` parameter into the `last_night` value by
  subtracting one day.

# [4.0.0] - 2019-12-18

### Changed

- Renamed one parameter from the `create_reservation_import` method `external_id` -> `listing_channel_reservation_id`, and it
  now accepts a `str` instead of an `int`.

# [3.0.0] - 2019-12-16

### Changed

- Removed four parameters from the `create_reservation_seed` method (`unit_id`, `arrival`, `departure`, and
  `discount_id`). These values are now extracted from the quote instead.

# [2.2.10] - 2019-12-09

### Added

- param `email` and `notes` are no longer required.

# [2.2.9] - 2019-11-26

### Added

- param `monthly_rent` and `management_fee` changed type from `int` to `float`.

# [2.2.8] - 2019-11-19

### Added

- param `phone2` added to reservation imports, it is a hidden post value not shown in the connect API.

# [2.2.7] - 2019-10-29

### Added

- New `get_language_list()` method, which uses [/v1/languages](https://connect.vacasa.com/#operation/get-languages-list) to get the languages offered in Connect.

# [2.2.6] - 2019-10-18

### Fixed

- param `auto_pay` changed to `autopay` for reservation imports, see [/v1/reservations-import](https://connect.vacasa.com/#operation/post-reservations-import)

# [2.2.5] - 2019-10-14

### Security

- Bump ecdsa from 0.13.2 to 0.13.3

# [2.2.4] - 2019-10-09

### Added

- New `create_reservation_import()` method, which uses [/v1/reservations-import](https://connect.vacasa.com/#operation/post-reservations-import)

# [2.2.3] - 2019-10-04

### Added

- param `created_by` to the `create_reservation_seed()` method, which uses [v1/reservations-seed](https://connect.vacasa.com/#operation/post-reservations-seed)

# [2.2.2] - 2019-09-25

### Added

- param `discount_id` to the `create_reservation_seed()` method, which uses [v1/reservations-seed](https://connect.vacasa.com/#operation/post-reservations-seed)

# [2.2.1] - 2019-09-23

### Added

- The `create_reservation_seed()` method, which uses [v1/reservations-seed](https://connect.vacasa.com/#operation/post-reservations-seed)

## [2.1.1] - 2019-08-23

### Fixed

- not calling .json() on financial patch call result

## [2.1.0] - 2019-08-19

### Added

- update_contact_finances()

## [2.0.0] - 2019-08-10

### Added

- New CHANGELOG.md added.

### Changes

- The `get_quote()` method now utilizes
  [v2 of the quotes endpoint](https://connect.vacasait.com/#operation/get-quote-v2).
