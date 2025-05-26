# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, VIOLATION
from pythonmop.builtin_instrumentation import InstrumentedFor
import pythonmop.spec.spec as spec

spec.DONT_MONITOR_PYTHONMOP = False


class ChangeListWhileIterating(Spec):
    """
    Checks if list is changed while iterating over it.
    """
    should_skip_in_sites = True

    def __init__(self):
        super().__init__()
        self.iterable_length_tracker = {}

        @self.event_before(call(InstrumentedFor, 'start'))
        def iteration_start(**kw):
            iterable = getKwOrPosArg('iterable', 1, kw)
            self.iterable_length_tracker[id(iterable)] = len(iterable)

        @self.event_after(call(InstrumentedFor, 'end'))
        def iteration_end(**kw):
            iterable = getKwOrPosArg('iterable', 1, kw)
            filename = getKwOrPosArg('filename', 2, kw)
            lineno = getKwOrPosArg('lineno', 3, kw)
            if id(iterable) in self.iterable_length_tracker:
                if len(iterable) != self.iterable_length_tracker[id(iterable)]:
                    return {
                        'verdict': VIOLATION,
                        'filename': filename,
                        'lineno': lineno,
                        'custom_message': f'list started with {self.iterable_length_tracker[id(iterable)]} elements, but ended with {len(iterable)} elements.'
                    }

    def match(self, call_file_name, call_line_num, args, kwargs, custom_message):
        print(
            f'Spec - {self.__class__.__name__}: list is changed while iterating over it. {custom_message}. file {call_file_name}, line {call_line_num}.')
# =========================================================================

'''
spec_in = ChangeListWhileIterating()
spec_in.create_monitor("D", True)

myList = ['a', 'b', 'c', 'd', 'e']
for i in myList:
    myList.remove(i)
'''
