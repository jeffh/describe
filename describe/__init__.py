"""A BDD Framework to help you verify your code is doing what you intended to do.

.. moduleauthor:: Jeff Hui <contrib@jeffhui.net>

"""

from value import Value
from mock import Mock, repository
from mock import args_filter as arg
from spec import Spec