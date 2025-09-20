# ============================== Define spec ==============================
from pythonmop import Spec, call
import pythonmop.spec.spec as spec

if not InstrumentedIterator:
    from pythonmop.builtin_instrumentation import InstrumentedIterator


class UnsafeListIterator(Spec):
    """
    Should not call next on iterator after modifying the list
    """
    class ListMeta:
        def __init__(self, l: list, length: int, warned: bool = False):
            self.l = l
            self.length = length
            self.warned = warned

    should_skip_in_sites = True

    def __init__(self):
        super().__init__()
        self.iterator_stack: list[self.ListMeta] = []

        @self.event_before(call(InstrumentedIterator, '__next__'))
        def next(**kw):
            iterable = kw['obj'].iterable

            if isinstance(iterable, list):
                try:
                    if (
                        len(self.iterator_stack) == 0
                        or id(iterable) != id(self.iterator_stack[-1].l)
                    ):
                        length = len(iterable)
                        self.iterator_stack.append(self.ListMeta(iterable, length))
                    elif len(self.iterator_stack) > 0:
                        list_meta: self.ListMeta = self.iterator_stack[-1]
                        if (
                            list_meta.warned is False
                            and len(iterable) < list_meta.length
                            and id(iterable) == id(list_meta.l)
                            and iterable == list_meta.l
                        ):
                            list_meta.warned = True
                            return True

                except Exception as e:
                    print(e)
            return False

        # TODO: add for loop end event for clean up memory
        @self.event_before(call(PymopForLoopTracker, 'for_loop_end'))
        def end_loop_list_changed(**kw):
            if len(self.iterator_stack) > 0:
                self.iterator_stack.pop()

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the list. file {call_file_name}, line {call_line_num}.')
# =========================================================================