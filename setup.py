from setuptools import setup, find_packages
import os
# Taken from setup.py in seaborn.
# temporarily redirect config directory to prevent matplotlib importing
# testing that for writeable directory which results in sandbox error in
# certain easy_install versions
os.environ["MPLCONFIGDIR"]="."

# Modified from from setup.py in seaborn.
try:
    from setuptools import setup
    _has_setuptools=True
except ImportError:
    from distutils.core import setup

def check_dependencies():
    to_install=[]
    try:
        import dabest
    except ImportError:
        to_install.append('dabest>=0.1')
    try:
        import numpy
    except ImportError:
        to_install.append('numpy')
    try:
        import scipy
    except ImportError:
        to_install.append('scipy')
    try:
        import matplotlib
    except ImportError:
        to_install.append('matplotlib')
    try:
        import pandas
        if int(pandas.__version__.split('.')[1])<20:
            to_install.append('pandas>=0.21')
    except ImportError:
        to_install.append('pandas>=0.21')
    try:
        import seaborn
    except ImportError:
        to_install.append('seaborn>=0.8.0')

    return to_install

if __name__=="__main__":

    installs=check_dependencies()
    setup(name='espresso',
        author='Joses Ho',
        author_email='joseshowh@gmail.com',
        version='0.1.2',
        description='Analysis of ESPRESSO experiments run on CRITTA.',
        packages=find_packages(),
        install_requires=installs,
        url='http://github.com/josesho/espresso',
        license='MIT'
        )
