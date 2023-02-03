from setuptools import setup

setup(
    name='VacasaConnect',
    version='4.27.1',
    description='A Python 3.6+ SDK for the connect.vacasa.com API.',
    packages=['vacasa.connect'],
    url='https://github.com/Vacasa/python-vacasa-connect-sdk',
    license='MIT',
    install_requires=[
        'pendulum==2.*',
        'requests>=2.20.0',
        'python-jose==3.*'
    ],
    extras_require={
        "cryptography": ['cryptography==38.0.*']
    },
    long_description=open('README.md').read()
)
