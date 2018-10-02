from distutils.core import setup

setup(
    name='VacasaConnect',
    version='0.3.0',
    description='A Python 3.6 SDK for the connect.vacasa.com API.',
    packages=['vacasa.connect'],
    url='https://github.com/Vacasa/python-vacasa-connect-sdk',
    license='MIT',
    install_requires=[
        'pendulum==2.*',
        'backoff~=1.6',
        'requests==2.*'
    ],
    long_description=open('README.md').read()
)
