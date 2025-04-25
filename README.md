# python-vacasa-connect-sdk
A Python 3.6+ SDK for interacting with the connect.vacasa.com API

# Prerequisites
Before you can use this SDK you'll need access to the 
[Vacasa Connect API](https://connect.vacasa.com/). 

# Getting Started
```python
# Initialize an instance of the VacasaConnect class using your credentials.
from vacasa.connect import VacasaConnect, IdpAuth

# Basic initialization with default connection pool settings
# Default values: pool_connections=10, pool_maxsize=10
connect = VacasaConnect(
    endpoint=CONNECT_API_ENDPOINT,
    auth=IdpAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        idp_url=IDP_URL
    ),
)

# Optional: Customize connection pool settings for better performance
connect = VacasaConnect(
    endpoint=CONNECT_API_ENDPOINT,
    auth=IdpAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        idp_url=IDP_URL,
        pool_connections=20,  # Optional: Number of connection pools (one per host)
        pool_maxsize=30      # Optional: Maximum simultaneous connections per host
    ),
    pool_connections=20,     # Optional: Number of connection pools (one per host)
    pool_maxsize=30         # Optional: Maximum simultaneous connections per host
)

# Get units
for unit in connect.get_units():
    print(unit)

# Get reviews
for review in connect.get_reviews():
    print(review)

# Generic get
# This is useful if you want to handle paging yourself
reviews = connect.get('reviews')
print(reviews)
```

# Dependencies
* [requests](https://github.com/requests/requests)
* [pendulum](https://github.com/sdispater/pendulum)
* [python-jose](https://python-jose.readthedocs.io/en/latest/)

# Development
```bash
# Install requirements https://pipenv.readthedocs.io/en/latest/
pipenv install

# Run tests
pytest
```

# Creating a Pull Request
Create a feature branch off the head of `master`.

Make sure you update the `CHANGELOG.md` as well as the version in `setup.py`.
