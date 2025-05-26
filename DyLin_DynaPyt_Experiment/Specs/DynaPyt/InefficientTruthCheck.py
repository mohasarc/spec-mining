# ============================== Define spec ==============================
from dynapyt.analyses.BaseAnalysis import BaseAnalysis

from typing import Any, Callable, List
from time import time_ns
import warnings

class InefficientTruthCheck(BaseAnalysis):
    """
    Checks for slow __bool__ and __len__ functions.
    Based on Zhang, Zejun, et al. "Faster or Slower? Performance Mystery of Python Idioms Unveiled with Empirical Evidence." arXiv preprint arXiv:2301.12633 (2023).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {}
        self.unique_event = {}
        self.violation = 0
        self.unique_violation = 0

        self.start_time = []
        self.threshold = 10000000  # 10 ms

    def function_enter(self, dyn_ast: str, iid: int, args: List[Any], name: str, is_lambda: bool) -> None:
        if name in ["__bool__", "__len__"]:
            self.start_time.append((iid, name, time_ns()))

    def function_exit(self, dyn_ast: str, iid: int, name: str, result: Any) -> Any:
        time_now = time_ns()
        if name in ["__bool__", "__len__"]:
            if len(self.start_time) == 0:
                return
            top = self.start_time.pop()
            if top[0] != iid or top[1] != name:
                return
            elapsed_time = time_now - top[2]
            if elapsed_time > self.threshold:
                # Add the event to the event dictionary
                if "violation" not in self.event:
                    self.event["violation"] = 1
                else:
                    self.event["violation"] += 1

                # Add the violation to the violation dictionary
                self.violation += 1

                # Find the file name and line number of the function in the original file
                call_file_name = dyn_ast
                call_line_num = BaseAnalysis.iid_to_location(self, dyn_ast, iid).start_line

                # Add the violation to the unique violation dictionary
                violation_key = f'{call_file_name}:{call_line_num}'
                if violation_key not in self.unique_event:
                    self.unique_event[violation_key] = 1
                    self.unique_violation += 1  # Increment the unique violation count
                else:
                    self.unique_event[violation_key] += 1

                # Print the violation message
                warnings.warn(
                    f'Spec - {self.__class__.__name__}: Slow {name} function took {elapsed_time/1000000} ms'
                    f'File {call_file_name}, line {call_line_num}.')

    def end_execution(self) -> None:
        # Count the number of events
        event_count = 0
        for key in self.event:
            event_count += self.event[key]

        # Write the statistics to a file
        with open(f'{self.__class__.__name__}_statistics.txt', 'w') as f:
            f.write(f"DynaPyt_Event_Count: {event_count}\n")
            f.write(f'DynaPyt_Event: {self.event}\n')
            f.write(f'DynaPyt_Unique_Event: {self.unique_event}\n')
            f.write(f"DynaPyt_Violation_Count: {self.violation}\n")
            f.write(f"DynaPyt_Unique_Violation_Count: {self.unique_violation}\n")

# =========================================================================
