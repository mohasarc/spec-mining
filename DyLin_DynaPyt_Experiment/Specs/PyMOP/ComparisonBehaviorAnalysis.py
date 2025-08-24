from pythonmop.builtin_instrumentation import class_creation_listener
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, get_all_subclasses
import pythonmop.spec.spec as spec
import inspect
import numpy as np


class ComparisonBehaviorAnalysis(Spec):
    """
    Detects bad comparison behavior for __eq__ and __ne__.
    """

    def __init__(self):
        super().__init__()

        for current_class in get_all_subclasses():
            self.instrument_class(current_class)

        def on_new_class(cls):
            self.instrument_class(cls)

        class_creation_listener.on_class_creation(on_new_class)

    def instrument_class(self, cls):
        try:
            # Some classes from libraries like pandas cannot be instrumented
            cls.__PYMOP_IMMUTABLE_TEST__ = True
            inspect.getmembers(cls)
        except Exception:
            return

        if cls.__eq__ is not object.__eq__:
            @self.event_after(call(cls, r'__eq__'))
            def eq_end(**kw):
                return self.check_all(kw, "Equal")

        if cls.__ne__ is not object.__ne__:
            @self.event_after(call(cls, r'__ne__'))
            def ne_end(**kw):
                return self.check_all(kw, "NotEqual")

    def is_excluded(self, val: any) -> bool:
        return (
            type(val) is int
            or type(val) is float
            or type(val) is str
            or type(val) is list
            or type(val) is set
            or type(val) is dict
            or type(val) is bool
            or isinstance(val, type(0.0))
            or isinstance(val, type(None))
            or isinstance(val, np.floating)
            or isinstance(val, np.ndarray)
        )

    def check_all(self, kw: dict, op: str):
        left = kw['obj']
        right = kw['args'][0]
        result = kw['return_val']

        if self.is_excluded(left) or self.is_excluded(right):
            return FALSE_EVENT

        try:
            if self.check_symmetry(left, right, op, result):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad symmetry for {op} with {left} {right}"
                }
            if self.check_stability(left, right, op, result):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad stability for {op}"
                }
            elif self.check_identity(left):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad identity {op} of {left} returned true when compared with None"
                }
            elif self.check_identity(right):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad identity {op} of {right} returned true when compared with None"
                }
            elif self.check_reflexivity(left):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad reflexivity {left} {op} to itself"
                }
            elif self.check_reflexivity(right):
                return {
                    'verdict': TRUE_EVENT,
                    'custom_message': f"bad reflexivity {right} {op} to itself"
                }
        except (ValueError, TypeError):
            # some libraries e.g. pandas do not allow to do all kinds of comparisons e.g. pandas.series == None
            return FALSE_EVENT
        
        return FALSE_EVENT

    def check_reflexivity(self, left) -> bool:
        return left != left

    def check_identity(self, left: any) -> bool:
        # This will raise ValueError for some types like pandas Series
        return left is not None and left == None

    def check_symmetry(self, left: any, right: any, op: any, res: bool) -> bool:
        if op == "Equal":
            return not ((left == right) == (right == left) == res)
        else:
            return not ((left != right) == (right != left) == res)

    def check_stability(self, left: any, right: any, op: any, normal: bool) -> bool:
        for _ in range(3):
            if op == "Equal":
                if (left == right) != normal:
                    return True
            else:
                if (left != right) != normal:
                    return True
        return False

    ere = '(eq_end|ne_end)'
    creation_events = ['eq_end', 'ne_end']

    def match(self, call_file_name, call_line_num, args, kwargs, custom_message):
        print(
            f'Spec - {self.__class__.__name__}: {custom_message}. file: {call_file_name}:{call_line_num}')