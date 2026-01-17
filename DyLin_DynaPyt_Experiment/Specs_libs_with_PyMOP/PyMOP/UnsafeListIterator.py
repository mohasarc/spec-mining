# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION

import collections


class UnsafeListIterator(Spec):
    """
    Should not call next on iterator after modifying the list
    """
    class ListMeta:
        def __init__(self, l: list, length: int):
            self.l = l
            self.length = length

    def __init__(self):
        super().__init__()
        self.iterator_stack: list[self.ListMeta] = []

        @self.event_before(call(PymopForLoopTracker, 'for_loop_start'))
        def for_loop_start(**kw):
            # Get the iterable from the for loop
            iterable = kw['args'][1]

            # Check if the iterable is a list
            if isinstance(iterable, collections.abc.Iterator) or isinstance(iterable, type({})):
                return False

            try:
                # Add the iterable to the stack
                length = len(iterable)
                self.iterator_stack.append(self.ListMeta(iterable, length))
            except Exception as e:
                pass

        # TODO: add for loop end event for clean up memory
        @self.event_before(call(PymopForLoopTracker, 'for_loop_end'))
        def end_loop_list_changed(**kw):
            # Get the iterable from the for loop
            iterable = kw['args'][1]

            # Check if the iterable is a list
            if isinstance(iterable, collections.abc.Iterator) or isinstance(iterable, type({})):
                return False

            try:
                # Get the iterable stored at the beginning of the loop
                list_meta: self.ListMeta = self.iterator_stack[-1]

                # Check if the iterable is the same as the iterable stored at the beginning of the loop
                if (
                    len(iterable) < list_meta.length
                    and id(iterable) == id(list_meta.l)
                    and iterable == list_meta.l
                ):
                    # Return a violation if the iterable is the same as the iterable stored at the beginning of the loop and modified
                    return {'verdict': VIOLATION, 
                            'custom_message': f"Should not call next on iterator after modifying the list at {kw['call_file_name']}, {kw['call_line_num']}.",
                            'filename': kw['call_file_name'],
                            'lineno': kw['call_line_num']}

                # Pop the iterable from the stack
                self.iterator_stack.pop()
            except Exception as e:
                pass

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Should not call next on iterator after modifying the list. file {call_file_name}, line {call_line_num}.')
# =========================================================================