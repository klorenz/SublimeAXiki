import sys, logging

logging.basicConfig()

from os.path import abspath, join, dirname
sys.path.insert(0, abspath(join(dirname(__file__), '..')))

import xiki

from xiki.tests import *

import unittest
unittest.main(module='test')