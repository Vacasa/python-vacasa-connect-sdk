from setuptools import setup

setup(
    name='VacasaConnect',
    version='5.0.0',
    description='A Python 3.8+ SDK for the connect.vacasa.com API.',
    packages=['vacasa.connect'],
    url='https://github.com/Vacasa/python-vacasa-connect-sdk',
    license='MIT',
    install_requires=[
        'pendulum==3.*',
        'requests>=2.20.0',
        'python-jose==3.*'
    ],
    extras_require={
        "cryptography": ['cryptography==38.0.*']
    },
    python_requires='>=3.8',
    long_description=open('README.md').read()
)
