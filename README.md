# python-vacasa-connect-sdk
A Python 3.6+ SDK for interacting with the connect.vacasa.com API

# Prerequisites
Before you can use this SDK you'll need access to the 
[Vacasa Connect API](https://connect.vacasa.com/). 

# Getting Started
```python
# Initialize an instance of the VacasaConnect class using your credentials.
from vacasa.connect import VacasaConnect, IdpAuth

connect = VacasaConnect(
    endpoint=CONNECT_API_ENDPOINT,
    auth=IdpAuth(
        config_endpoint=OIDC_CONFIG_ENDPOINT,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        audience=OIDC_AUDIENCE,
        scopes=[
            # see OIDC_CONFIG_ENDPOINT for supported scopes
            LIST,
            OF,
            REQUESTED,
            SCOPES,
        ]
    ),
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
