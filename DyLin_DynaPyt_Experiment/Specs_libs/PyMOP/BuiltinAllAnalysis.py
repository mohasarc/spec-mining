# ============================== Define spec ==============================
from pythonmop import Spec, VIOLATION, call
import builtins


class BuiltinAllAnalysis(Spec):
    """
    This is used to check if all builtins are used in the code.
    Converted from DyLin's BuiltinAllAnalysis checker.
    """

    def __init__(self):
        super().__init__()

        @self.event_after(call(builtins, 'all'))
        def violation(**kw):
            arg = kw['args'][0]
            if isinstance(arg, type([])):
                flattened = self._flatten(arg)
                if len(flattened) == 0 and kw['return_val'] == True:
                    return {'verdict': VIOLATION, 
                        'custom_message': f"Potentially unintended result for any() call at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}
            
        @self.event_after(call(builtins, 'any'))
        def violation(**kw):
            arg = kw['args'][0]
            if isinstance(arg, type([])):
                flattened = self._flatten(arg)
                if len(flattened) == 0 and kw['return_val'] == True:
                    return {'verdict': VIOLATION, 
                        'custom_message': f"Potentially unintended result for any() call at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}

    def _flatten(self, l):
        new_list = []
        for i in l:
            if isinstance(i, type([])):
                new_list = new_list + self._flatten(i)
            else:
                new_list.append(i)
        return new_list

    def match(self, call_file_name, call_line_num):
        print(f'Spec - {self.__class__.__name__}: Potentially unintended result for any() call at file {call_file_name}, line {call_line_num}.')
# =========================================================================
"""
spec_instance = BuiltinAllAnalysis()
spec_instance.create_monitor('D')

assert all([]) == True  # Violation
"""