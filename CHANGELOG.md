# CHANGELOG

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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


