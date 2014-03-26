import logging
log = logging.getLogger('xiki')
log.setLevel(logging.DEBUG)

from .core import XikiContext
from .path import XikiPath
from .contexts import *