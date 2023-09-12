from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='pyelo',
    version='0.1.0',
    description='Package FEA unit control using VISA library',
    long_description=readme,
    author='Martin Zobač',
    author_email='zobac@isibrno.cz',
    url='',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
