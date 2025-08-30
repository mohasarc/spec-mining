# ============================== Define spec ==============================
import nntplib
from pythonmop import Spec, call, getKwOrPosArg, TRUE_EVENT, FALSE_EVENT
import pythonmop.spec.spec as spec
import random

spec.DONT_MONITOR_SITE_PACKAGES = True

class WrongTypeAddedAnalysis(Spec):
    """
    Warns if a value of a different type is added to a list/set that was previously homogeneous.
    """
    should_skip_in_sites = True

    def __init__(self):
        super().__init__()

        self.THRESHOLD = 10

        @self.event_before(call(list, 'append'))
        def check_append(**kw):
            return self._check_add("append", **kw)

        @self.event_before(call(list, 'add'))
        def check_add(**kw):
            return self._check_add("add", **kw)

        @self.event_before(call(list, 'insert'))
        def check_insert(**kw):
            return self._check_add("insert", **kw)

        @self.event_before(call(list, 'extend'))
        def check_extend(**kw):
            return self._check_add("extend", **kw)

        @self.event_before(call(PymopArithmeticOperatorTracker, r'__pymop__add__|__pymop__iadd__'))
        def check_add_assign(**kw):
            if len(kw['args']) < 3:
                return FALSE_EVENT

            return self._check_add("add_assign", **kw)

    def _check_add(self, method, **kw):
        if method == "add_assign":
            left = kw['args'][1]
        else:
            left = kw['obj']

        if not hasattr(left, '__len__') or len(left) <= self.THRESHOLD:
            return FALSE_EVENT

        if method in ('append', 'add'):
            right = getKwOrPosArg('object', 1, kw)
        elif method == 'insert':
            right = getKwOrPosArg('object', 2, kw)
        elif method == 'extend':
            right = getKwOrPosArg('object', 1, kw)
            if hasattr(right, '__iter__'):
                right = list(right)
            else:
                return FALSE_EVENT
        elif method == "add_assign":
            right = kw['args'][2]
            if hasattr(right, '__iter__'):
                right = list(right)
            else:
                return FALSE_EVENT
        else:
            return FALSE_EVENT

        type_to_check = type(random.choice(list(left)))

        # Optimization to reduce overhead for large lists sample size has to be lower than threshold from DyLin
        left_sample = random.sample(list(left), self.THRESHOLD)
        consistent_same_type_left = all(isinstance(n, type_to_check) for n in left_sample)

        if consistent_same_type_left:
            if method in ('append', 'add', 'insert'):
                if not isinstance(right, type_to_check):
                    return TRUE_EVENT
            elif method == 'extend':
                if hasattr(right, '__len__') and len(right) >= self.THRESHOLD:
                    right_sample = random.sample(list(right), self.THRESHOLD)
                    consistent_same_type_right = all(isinstance(n, type_to_check) for n in right_sample)
                    if not consistent_same_type_right:
                        return TRUE_EVENT
            elif method == "add_assign":
                if len(right) > 0:
                    right_sample_type = type(right[0])
                    if right_sample_type != type_to_check:
                        return TRUE_EVENT

        return FALSE_EVENT

    ere = 'check_append|check_add|check_insert|check_extend|check_add_assign'
    creation_events = ['check_append', 'check_add', 'check_insert', 'check_extend', 'check_add_assign']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Added potentially wrong type to a previously homogeneous list/set. file {call_file_name}, line {call_line_num}.')

# ============================== Example Usage ==============================
'''
spec_instance = WrongTypeAddedAnalysis()
spec_instance.create_monitor("D")

lst = list(range(20))
lst.append(42)        # ✅ same type (int)
lst.append("oops")    # 🚨 different type (str), will trigger the violation

lst = list(range(8))
lst.append(42)        # ✅ same type (int)
lst.append("oops")    # 🚨 different type (str), but not detected because of threshold

lst = list(range(15))
lst.extend([42, 32])        # ✅ same type (int)
lst.extend([48, "oops"])    # 🚨 different type (str)

lst = list(range(15))
lst.insert(0, 42)        # ✅ same type (int)
lst.insert(0, "oops")    # 🚨 different type (str)
'''