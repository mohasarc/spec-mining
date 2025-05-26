from dynapyt.analyses.BaseAnalysis import BaseAnalysis

from typing import Any
import operator
import numpy as np
import warnings

class ComparisonBehaviorAnalysis(BaseAnalysis):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {}
        self.unique_event = {}
        self.violation = 0
        self.unique_violation = 0

        self.excluded_types = [type(0.0), type(None)]
        self.stack_levels = 20
        self.cache = {}

    """
    TODO:
    don't check for all comparisons only if
    "__eq__",
    "__ge__",
    "__gt__",
    "__le__",
    "__ne__",
    "__lt__",
    are implemented by hand
    """

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

    def equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # print(f"{self.analysis_name} equal {iid}")
        self.check_all(dyn_ast, iid, left, "Equal", right, result)

    def not_equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # print(f"{self.analysis_name} not equal {iid}")
        self.check_all(dyn_ast, iid, left, "NotEqual", right, result)

    def check_all(self, dyn_ast: str, iid: int, left: Any, op: str, right: Any, result: Any) -> bool:
        if op != "Equal" and op != "NotEqual":
            return None

        if self.is_excluded(left) or self.is_excluded(right):
            return None

        try:
            if self.check_symmetry(left, right, op, result):
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
                    f'Spec - {self.__class__.__name__}: Bad symmetry for {op} with {left} {right}. '
                    f'File {call_file_name}, line {call_line_num}.')

            if self.check_stability(left, right, op, result):
                # Removed as DyLin does not use this analysis
                '''
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
                    f'Spec - {self.__class__.__name__}: Bad stability for {op}. '
                    f'File {call_file_name}, line {call_line_num}.')
                '''
                pass

            elif self.check_identity(left):
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
                    f'Spec - {self.__class__.__name__}: Bad identity {op} of {left} returned true when compared with None. '
                    f'File {call_file_name}, line {call_line_num}.')

            elif self.check_identity(right):
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
                    f'Spec - {self.__class__.__name__}: Bad identity {op} of {left} returned true when compared with None. '
                    f'File {call_file_name}, line {call_line_num}.')

            elif self.check_reflexivity(left):
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
                    f'Spec - {self.__class__.__name__}: Bad reflexivity {left} {op} to itself. '
                    f'File {call_file_name}, line {call_line_num}.')

            elif self.check_reflexivity(right):
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
                    f'Spec - {self.__class__.__name__}: Bad reflexivity {right} {op} to itself. '
                    f'File {call_file_name}, line {call_line_num}.')

        except ValueError:
            # some libraries e.g. pandas do not allow to do all kinds of comparisons e.g. pandas.series == None
            return

    def check_reflexivity(self, left) -> bool:
        return left != left

    def check_identity(self, left: Any) -> bool:
        return left is not None and left == None

    def check_symmetry(self, left: Any, right: Any, op: Any, res: bool) -> bool:
        # (3 == 4) == (4 == 3)
        if op == "Equal":
            return not ((left == right) == (right == left) == res)
        else:
            return not ((left != right) == (right != left) == res)

    def check_stability(self, left: Any, right: Any, op: Any, normal: bool) -> bool:
        for _ in range(3):
            if op == "Equal":
                if (left == right) != normal:
                    return True
            else:
                if (left != right) != normal:
                    return True
        return False

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

