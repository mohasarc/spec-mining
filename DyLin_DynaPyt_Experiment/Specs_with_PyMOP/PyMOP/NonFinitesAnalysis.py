from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import numpy as np
import pandas as pd


class NonFinitesAnalysis(Spec):
    """
    Checks for NaNs, infs, and -infs in numpy arrays.
    """

    def __init__(self):
        super().__init__()

        @self.event_before(call(PymopFuncCallTracker, 'after_call'))
        def non_finite_op(**kw):
            return_val = kw['args'][1]
            args = kw['args'][2]
            kwargs = kw['args'][3]
            no_nan_in_input = True

            for arg in args:
                if self.check_np_issue_found(arg):
                    no_nan_in_input = False
                    return TRUE_EVENT
            
            for arg in kwargs:
                if self.check_np_issue_found(arg):
                    no_nan_in_input = False
                    return TRUE_EVENT

            if self.check_np_issue_found(return_val):
                if no_nan_in_input:
                    return TRUE_EVENT

            return FALSE_EVENT

    # copied as is from https://github.com/sola-st/DyLin/blob/main/src/dylin/analyses/NonFinitesAnalysis.py
    def can_be_checked_with_numpy(self, value: any) -> bool:
        return isinstance(value, np.ndarray) or isinstance(value, pd.DataFrame)

    # copied as is from https://github.com/sola-st/DyLin/blob/main/src/dylin/analyses/NonFinitesAnalysis.py
    def numpy_check_not_finite(self, df: any) -> bool:
        try:
            is_inf = np.isinf(df)
            try:
                # need to extract values from pandas.Dataframes first
                result = True in is_inf.values
                return result
            except AttributeError as e:
                return True in is_inf
        except TypeError as e:
            return False

    # copied as is from https://github.com/sola-st/DyLin/blob/main/src/dylin/analyses/NonFinitesAnalysis.py
    def check_np_issue_found(self, value: any) -> bool:
        if self.can_be_checked_with_numpy(value) and self.numpy_check_not_finite(value):
            return True
        return False

    ere = 'non_finite_op+'
    creation_events = ['non_finite_op']

    def match(self, call_file_name, call_line_num):
        print(f"Spec - {self.__class__.__name__}: Non-finite value found in argument. file {call_file_name}, line {call_line_num}.")
# =========================================================================

'''
theSpec = NonFinitesAnalysis()
theSpec.create_monitor('D', True, True)

nparray = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

new_nparray = np.add(nparray, np.inf)
new_nparray = np.add(nparray, -np.inf)

df = pd.DataFrame(nparray)
df.add(1, axis=0)

df.add(np.inf, axis=0)
df.add(-np.inf, axis=0)

df.add(np.inf, axis=1)
df.add(-np.inf, axis=1)

df.add(np.inf, axis=0)
df.add(-np.inf, axis=0)
'''