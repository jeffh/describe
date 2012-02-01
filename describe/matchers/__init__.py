from describe.matchers.functional_matchers import *
from describe.matchers.core import matcher_repository, matcher


def __load_matchers():
	"Load point for default matchers"
	import describe.matchers.class_matchers
	import describe.matchers.change
__load_matchers()
