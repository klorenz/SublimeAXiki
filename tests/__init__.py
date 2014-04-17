from imp import reload

from imp import reload

# make sure newest version of test_main is loaded
from . import test_main
reload(test_main)

# here you also could reload modules under test

# load testcases

from .test_main import *