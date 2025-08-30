# ============================== Define spec ==============================
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

        self.tracked = {}  # id(obj) -> {"sample": [types...], "type": dominant_type, "threshold": N}
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
            if len(kw['args']) >= 3:
                left_list = kw['args'][1]
            else:
                return FALSE_EVENT

            if not isinstance(left_list, type([])):
                return FALSE_EVENT

            return self._check_add("add_assign", **kw)

    def _check_add(self, method, **kw):
        if method == "add_assign":
            obj = kw['args'][1]
        else:
            obj = kw['obj']

        if not hasattr(obj, '__len__') or len(obj) <= self.THRESHOLD:
            return FALSE_EVENT

        if method in ('append', 'add'):
            arg = getKwOrPosArg('object', 1, kw)
        elif method == 'insert':
            arg = getKwOrPosArg('object', 2, kw)
        elif method == 'extend':
            arg = getKwOrPosArg('object', 1, kw)
            if hasattr(arg, '__iter__'):
                arg = list(arg)
            else:
                return FALSE_EVENT
        elif method == "add_assign":
            arg = kw['args'][2]
            if hasattr(arg, '__iter__'):
                arg = list(arg)
            else:
                return FALSE_EVENT
        else:
            return FALSE_EVENT

        obj_id = id(obj)

        if obj_id not in self.tracked or len(self.tracked[obj_id]['sample']) < self.THRESHOLD:
            self.tracked[obj_id] = {
                "sample": random.sample(list(obj), min(len(obj), self.THRESHOLD)),
                "threshold": len(obj),
            }
            sample = self.tracked[obj_id]['sample']
            types_in_sample = [type(x) for x in sample]
            dominant_type = types_in_sample[0] if all(isinstance(x, types_in_sample[0]) for x in sample) else None
            self.tracked[obj_id]['type'] = dominant_type

        dominant_type = self.tracked[obj_id]['type']


        if dominant_type is not None:
            added_values = arg if isinstance(arg, list) else [arg]
            if any(not isinstance(item, dominant_type) for item in added_values):
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