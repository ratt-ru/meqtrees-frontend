#!/usr/bin/env python3

import os
import sys
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

try:
    from qtpy import QtCore
except ImportError:
    print("Cannot import PyQt. This is not available from PyPI and has "
          "to be installed from your distribution streams")
    sys.exit(1)

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils not to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in list(INSTALL_SCHEMES.values()):
    scheme['data'] = scheme['purelib']

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

packages = []
data_files = []
scripts = ["scripts/meqbrowser.py"]
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('MeqGUI'):
    # Ignore dirnames that start with '.'
    dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != '__pycache__']
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

install_requires = [
    'numpy',
    'python-casacore',
    'six',
    'configparser',
    'PythonQwt>=0.10.1',
    'pyqt'
] + [ # meqtrees sister packages    
    'purr',
    'astro-kittens',
    'meqtrees-cattery',
    'astro-tigger-lsm',
    'owlcat',
]

setup(name='meqtrees-frontend',
      version='1.0.0',
      python_requires='>=3.6.0',
      description='MeqTrees-based frameworks for simulation and calibration of radio interferometers ',
      author='Oleg Smirnov',
      author_email='osmirnov@gmail.com',
      url='https://github.com/ska-sa/meqtrees-cattery',
      packages=packages,
      scripts=scripts,
      data_files=data_files,
      install_requires=install_requires,
      long_description=long_description,
      long_description_content_type='text/markdown'
     )
