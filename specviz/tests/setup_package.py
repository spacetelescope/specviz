# import os

# If this package has tests data in the tests/data directory, add them to
# the paths here, see commented example
paths = ['coveragerc',
#         os.path.join('data', '*fits')
         ]

def get_package_data():
    """
    Function to return the a mapping of defining the paths for this package's
    tests.
    """
    return {
        _ASTROPY_PACKAGE_NAME_ + '.tests': paths}
