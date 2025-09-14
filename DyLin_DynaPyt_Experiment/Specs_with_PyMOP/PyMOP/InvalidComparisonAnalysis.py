# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, getKwOrPosArg
import numpy as np
import types
import math


class InvalidComparisonAnalysis(Spec):
    """
    Detects invalid or suspicious comparisons between incompatible or misleading types.
    Flags float comparisons involving infs or near equality, comparisons with functions, or type mismatches.
    """
    should_skip_in_sites = True

    def __init__(self):
        super().__init__()

        # PymopComparisonTracker will be injected by PyMOP at runtime when using ast strategy.
        # This spec is not supported with other strategies.
        @self.event_after(call(PymopComparisonTracker, r'(__pymop__eq__|__pymop__ne__)'))
        def after_comparison(**kw):
            left = getKwOrPosArg('left', 1, kw)
            right = getKwOrPosArg('right', 2, kw)

            if left is None or right is None:
                return FALSE_EVENT

            if self._is_float(left) or self._is_float(right):
                if self._is_inf(left) or self._is_inf(right):
                    return {
                        'verdict': TRUE_EVENT,
                        'custom_message': 'float comparison with inf'
                    }

                if self._are_nearly_equal(left, right):
                    return {
                        'verdict': TRUE_EVENT,
                        'custom_message': 'float comparison with nearly equal floats'
                    }

            if self._compare_functions(left, right):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': 'comparison between function and non-function'
                }

            if self._compare_types(left, right):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': 'comparison between incompatible types'
                }

            return FALSE_EVENT

    def _is_float(self, x):
        return isinstance(x, float) or isinstance(x, np.floating)

    def _is_inf(self, x):
        return self._is_float(x) and np.isinf(x)

    def _are_nearly_equal(self, a, b):
        return (
            self._is_float(a)
            and self._is_float(b)
            and a != b
            and math.isclose(a, b, rel_tol=1e-8)
        )

    def _compare_functions(self, left, right):
        left_is_func = isinstance(left, types.FunctionType)
        right_is_func = isinstance(right, types.FunctionType)

        left_is_slot = isinstance(left, type(int.__abs__))
        right_is_slot = isinstance(right, type(int.__abs__))

        if left_is_func != right_is_func and not (left_is_slot or right_is_slot):
            return True
        return False

    def _compare_types(self, left, right):
        return isinstance(left, type) and isinstance(right, type) and left != right

    ere = '(after_comparison)+'
    creation_events = ['after_comparison']

    def match(self, call_file_name, call_line_num, args, kwargs, custom_message):
        print(f"Spec - {self.__class__.__name__}: Suspicious or invalid comparison because of {custom_message}. file {call_file_name}, line {call_line_num}.")


# ============================== Example Usage ==============================
'''
spec_instance = InvalidComparisonAnalysis()
spec_instance.create_monitor("D")

def f(x):
    return x + 1

1 == f  # 🚨 comparison between int and function (forgot to call f)

1 == 1.00000000001  # 🚨 nearly equal floats

float('inf') == 10.0  # 🚨 inf involved

1 != f  # 🚨 comparison between int and function (forgot to call f)


1.0 < 1.000000000001  # 🚨 comparison between int and function (forgot to call f)
1.0 >= 1.000320000001  # 🚨 comparison between int and function (forgot to call f)
1.0 <= 1.002444220001  # 🚨 comparison between int and function (forgot to call f)

a = 1
b = 1
a is b 

f(1) == 2  # 🚨 comparison between int and function (forgot to call f)

'''