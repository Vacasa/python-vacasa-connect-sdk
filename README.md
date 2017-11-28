# python-vacasa-connect-sdk
A Python 3.6 SDK for interacting with the connect.vacasa.com API

# Prerequisites
Before you can use this SDK you'll need access to the 
[Vacasa Connect API](https://connect.vacasa.com/). 

# Getting Started
```python
# Initialize an instance of the VacasaConnect class using your credentials.
from vacasaconnect import VacasaConnect
connect = VacasaConnect('https://connect.vacasa.com/', 'your_key', 'your_secret')

# Get units
for unit in connect.get_units():
    print(unit)
```

# Development
```bash
# Install requirements
pip install -r requirements.txt

# Run tests
pytest
```
