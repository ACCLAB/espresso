from setuptools import setup, find_packages
import os
# Taken from setup.py in seaborn.
# temporarily redirect config directory to prevent matplotlib importing
# testing that for writeable directory which results in sandbox error in
# certain easy_install versions
os.environ["MPLCONFIGDIR"]="."


DESCRIPTION = 'Package for analysis of ESPRESSO experiments'
LONG_DESCRIPTION = """\
This Python package enables analysis of feeding experiments done on the
ESPRESSO rigs, and monitored via CRITTA.

For use in the Claridge-Chang lab.
"""

# Modified from from setup.py in seaborn.
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup



def need_to_install(module, version):
    desired_major_version = int(version.split('.')[0])
    desired_minor_version = int(version.split('.')[1])
    try:
        desired_patch = int(version.split('.')[2])
        patch_stated = True
    except IndexError:
        patch_stated = False

    INSTALLED_VERSION_MAJOR = int(module.__version__.split('.')[0])
    INSTALLED_VERSION_MINOR = int(module.__version__.split('.')[1])
    try:
        INSTALLED_VERSION_PATCH = int(version.split('.')[2])
    except IndexError:
        pass

    if INSTALLED_VERSION_MAJOR < desired_major_version:
        return True

    elif INSTALLED_VERSION_MAJOR == desired_major_version and \
         INSTALLED_VERSION_MINOR < desired_minor_version:
        return True

    else:
        return False



def check_dependencies():
    from importlib import import_module

    modules = {'numpy'      : '1.15',
               'scipy'      : '1.2',
               'pandas'     : '0.24',
               'matplotlib' : '3.0',
               'seaborn'    : '0.9',
               'dabest'     : '0.2.2'}
    to_install = []

    for module, version in modules.items():
        try:
            my_module = import_module(module)

            if need_to_install(my_module, version):
                to_install.append("{}>={}".format(module, version))

        except ImportError:
            to_install.append("{}>={}".format(module, version))

    return to_install


if __name__=="__main__":

    installs=check_dependencies()

    setup(
        name='espresso',
        author='Joses Ho',
        author_email='joseshowh@gmail.com',
        version='0.7.0',
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=installs,
        url='https://www.github.com/ACCLAB/espresso',
        )
