# ============================== Define spec ==============================
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT, End, getKwOrPosArg
import builtins


class InPlaceSortAnalysis(Spec):
    """
    Inplace sort is more efficient that sorted(). prefer using inplace if the original list is not needed.
    """

    # should_skip_in_sites = True

    def __init__(self):
        super().__init__()
        self.stored_lists = []
        self.threshold = 1000

        @self.event_before(call(builtins, 'sorted'))
        def list_sorted(**kw):
            iterable = getKwOrPosArg('iterable', 0, kw)
            if hasattr(iterable, "__len__") and len(iterable) > self.threshold:
                self.stored_lists.append(id(iterable))

        # read related events
        @self.event_before(call(list, r'(__len__|__contains__|__getitem__|__eq__|__ne__|__lt__|__le__|__gt__|__ge__|__iter__)' ))
        def list_used(**kw):
            list_id = id(kw['args'][0])
            if list_id in self.stored_lists:
                self.stored_lists.remove(list_id)

        @self.event_before(call(End, 'end_execution'))
        def end_execution(**kw):
            if len(self.stored_lists) > 0:
                print(f'Spec - {self.__class__.__name__}: Unnessecary use of sorted() call for lists: {self.stored_lists}.')

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