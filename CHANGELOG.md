# CHANGELOG

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- param `auto_pay` changed to `autopay` for reservation imports, see  [/v1/reservations-import](https://connect.vacasa.com/#operation/post-reservations-import)

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
