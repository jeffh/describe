from describe.matchers import class_matchers as matchers

__all__ = 'includes contains be_instance_of be_an_instance_of be_a_subclass_of'.split(' ') + \
    'be_subclass_of be_gt be_greater_than be_gte be_ge be_greater_than_or_equal_to be_lt be_less_than'.split(' ') + \
    'be_lte be_le be_less_than_or_equal_to raise_error'.split(' ')

includes = contains = matchers.IsInMatcher.as_function()
#be_eq = be_equal_to = be_equal = EqualityMatcher.as_function()
be_instance_of = be_an_instance_of = matchers.InstanceMatcher.as_function()
be_a_subclass_of = be_subclass_of = matchers.SubclassMatcher.as_function()
be_gt = be_greater_than = matchers.GreaterThanMatcher.as_function()
be_gte = be_ge = be_greater_than_or_equal_to = matchers.GreaterThanOrEqualToMatcher.as_function()
be_lt = be_less_than = matchers.LessThanMatcher.as_function()
be_lte = be_le = be_less_than_or_equal_to = matchers.LessThanOrEqualToMatcher.as_function()
raise_error = matchers.ExceptionMatcher.as_function()
be_equal = be_equal_to = matchers.IsMatcher.as_function()
