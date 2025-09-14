# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, End, getKwOrPosArg
import builtins


class InPlaceSortAnalysis(Spec):
    """
    Inplace sort is more efficient that sorted(). prefer using inplace if the original list is not needed.
    """

    def __init__(self):
        super().__init__()
        self.threshold = 1

        @self.event_before(call(builtins, 'sorted'))
        def list_sorted(**kw):
            iterable = getKwOrPosArg('iterable', 0, kw)

            if hasattr(iterable, "__len__") and len(iterable) > self.threshold:
                return {
                    "verdict": TRUE_EVENT,
                    "param_instance": iterable,
                }
        
            return FALSE_EVENT

        # read related events
        @self.event_before(call(list, r'(__len__|__contains__|__getitem__|__eq__|__ne__|__lt__|__le__|__gt__|__ge__|__iter__)' ))
        def list_used(**kw):
            return TRUE_EVENT

        @self.event_before(call(End, 'end_execution'))
        def end_execution(**kw):
            return TRUE_EVENT
    
    fsm = """
        s0 [
            list_sorted -> s1
            list_used -> s2
        ]
        s1 [
            list_used -> s2
            end_execution -> s3
        ]
        s2 [
            list_sorted -> s1
            default s2
        ]
        s3 []
        alias match = s3
    """
    creation_events = ['list_sorted', 'list_used']

    def match(self, call_file_name, call_line_num):
        # TODO: Provide more information about the lists that are being sorted.
        print(f'Spec - {self.__class__.__name__}: Unnessecary use of sorted() call at file {call_file_name}, line {call_line_num}.')
# =========================================================================

"""
spec_instance = InPlaceSortAnalysis()
spec_instance.create_monitor('D')

a = list(range(0, 32131))
b = list(range(0, 32132))
c = list(range(231, 321033))
d = list(range(0, 32134))
e = list(range(0, 32135))
f = list(range(0, 32136))
h = list(range(0, 32137))

sorted(a)  # DyLin warn
x = sorted(b)  # DyLin warn
y = sorted(c)  # DyLin warn
h = sorted(h, reverse=True)  # DyLin warn

d.sort()
z = sorted(e)
e.append([])
k = sorted(f)
f
h
print('end')
End().end_execution()
"""