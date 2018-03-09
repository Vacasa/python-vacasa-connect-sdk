# python-vacasa-connect-sdk
A Python 3.6 SDK for interacting with the connect.vacasa.com API

# Prerequisites
Before you can use this SDK you'll need access to the 
[Vacasa Connect API](https://connect.vacasa.com/). 

# Getting Started
```python
# Initialize an instance of the VacasaConnect class using your credentials.
from vacasa.connect import VacasaConnect
connect = VacasaConnect('your_key', 'your_secret')

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

# Development
```bash
# Install requirements
pip install -r requirements.txt

# Run tests
pytest
```
