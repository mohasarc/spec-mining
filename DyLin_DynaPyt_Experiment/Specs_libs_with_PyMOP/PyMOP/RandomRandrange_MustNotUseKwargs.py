# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION
import random


class RandomRandrange_MustNotUseKwargs(Spec):
    """
    Keyword arguments should not be used because they can be interpreted in unexpected ways
    source: https://docs.python.org/3/library/random.html#random.randrange
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(random, 'randrange'))
        def test_verify(**kw):
            kwargs = kw['kwargs']
            if kwargs:
                return {'verdict': VIOLATION, 
                        'custom_message': f"Keyword arguments should not be used in random.randrange because they can be interpreted in unexpected ways at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Keyword arguments should not be used in random.randrange because they '
            f'can be interpreted in unexpected ways. in {call_file_name} at line {call_line_num}')


# =========================================================================

'''
spec_instance = RandomRandrange_MustNotUseKwargs()
spec_instance.create_monitor("B")
random.randrange(10)
random.randrange(10, 100, step=2)
# spec_instance.get_monitor().refresh_monitor() # only used in A
'''