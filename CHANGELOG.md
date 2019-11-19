# CHANGELOG

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
# [2.2.7] - 2019-10-18
### Added
- param `phone2` added to reservation imports, it is a hidden post value not shown in the connect API.

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


