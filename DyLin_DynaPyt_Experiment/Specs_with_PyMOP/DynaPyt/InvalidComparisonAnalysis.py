from dynapyt.analyses.BaseAnalysis import BaseAnalysis

import operator
import types
from typing import Any, Callable
import math
import numpy as np
import warnings

"""
Name: 
Invalid Comparison

Source:
https://blog.sonarsource.com/sonarcloud-finds-bugs-in-high-quality-python-projects/

Test description:
Using the == operator on incompatible types will not fail but always returns False.
Python documentation for rich comparisons: https://docs.python.org/2/reference/datamodel.html?highlight=__lt__#object.__eq__

Why useful in a dynamic analysis approach:
Static analysis is often not able to infer the types correctly and thus may have several false negatives / false positives.

Discussion:
Consider these cases: https://github.com/PyCQA/pylint/blob/main/tests/functional/s/singleton_comparison.py and https://vald-phoenix.github.io/pylint-errors/plerr/errors/basic/R0123
and https://vald-phoenix.github.io/pylint-errors/plerr/errors/basic/R0124

TODO: fix testcases
"""


class InvalidComparisonAnalysis(BaseAnalysis):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {}
        self.unique_event = {}
        self.violation = 0
        self.unique_violation = 0

        self.nmb_comparisons = 0
        self.stack_levels = 20
        self.float_comparisons_to_check = [
            "Equal",
            "GreaterThan",
            "GreaterThanEqual",
            "LessThan",
            "LessThanEqual",
            "NotEqual",
        ]

    def not_equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        self.equal(dyn_ast, iid, left, right, not result)

    def equal(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # print(f"{self.analysis_name} comparison {iid}")
        self.nmb_comparisons += 1
        try:
            if (self._is_float(left) or self._is_float(right)):
                if self.check_inf(left) or self.check_inf(right):
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
                        f'Spec - {self.__class__.__name__}: inf floats left {left} right {right} in comparison used'
                        f'File {call_file_name}, line {call_line_num}.')
                    '''
                    pass

                if self.compare_floats(left, right):
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
                        f'Spec - {self.__class__.__name__}: compared floats nearly equal {left} and {right}'
                        f'File {call_file_name}, line {call_line_num}.')

            if self.compare_types(left, right):
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
                    f'Spec - {self.__class__.__name__}: compared with type {left} and {right}'
                    f'File {call_file_name}, line {call_line_num}.')

            if self.compare_funct(left, right):
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
                    f'Spec - {self.__class__.__name__}: compared with function {left} and {right}'
                    f'File {call_file_name}, line {call_line_num}.')

        except ValueError:
            return

    def _is_float(self, f: any) -> bool:
        return isinstance(f, float) or isinstance(f, np.floating)

    def check_nan(self, num: float) -> bool:
        # np.isnan handles python builtin floats and numpy floats
        return self._is_float(num) and np.isnan(num)

    def check_inf(self, num: float) -> bool:
        # np.isnan handles python builtin floats and numpy floats
        return self._is_float(num) and np.isinf(num)

    def compare_floats(self, left: float, right: float) -> bool:
        return (
            self._is_float(left) and self._is_float(right) and left != right and math.isclose(left, right, rel_tol=1e-8)
        )

    # Change this to analyse iff == returns false but is returns true -> flag issue
    # is compares ids, if they are the same == should return true as well
    def compare_diff_in_operator(self, left: Any, right: Any, op: Callable) -> bool:
        if type(left) == bool or type(right) == bool:
            res = op(left, right)
            if op == operator.eq and (left is right) != res:
                return True
            elif op == operator.ne and (left is not right) != res:
                return True
        return False

    def in_type_mismatch(self, left: Any, right: Any) -> bool:
        if (type(left) is list and type(right) is list) or (type(left) is set and type(right) is set):
            if len(left) == 1 and next(iter(left)) in right:
                return True
        return False

    """
    https://pylint.pycqa.org/en/latest/user_guide/messages/warning/comparison-with-callable.html
    """

    def compare_funct(self, left: Any, right: Any) -> bool:
        left_is_func = isinstance(left, types.FunctionType)
        right_is_func = isinstance(right, types.FunctionType)

        # ignore wrapper_descriptor types which are builtin functions implemented in C
        left_is_slot_type = isinstance(left, type(int.__abs__))
        right_is_slot_type = isinstance(right, type(int.__abs__))
        # xor
        if (
            left_is_func != right_is_func
            and not (left_is_slot_type or right_is_slot_type)
            and left is not None
            and right is not None
        ):
            return True
        return False

    """
    unidiomatic typecheck https://pylint.pycqa.org/en/latest/user_guide/messages/convention/unidiomatic-typecheck.html
    """

    def compare_types(self, left: Any, right: Any) -> bool:
        left_is_type = isinstance(left, type)
        right_is_type = isinstance(right, type)

        if left_is_type and right_is_type and left != right:
            return True
        return False

    """
    There are cases where obj == None / None == obj can return true even though object has an identity, i.e. is not None.
    E.g. equals operator is overloaded. Preferred method is obj is None
    """

    def compared_with_none(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        if isinstance(left, type(None)) or isinstance(right, type(None)):
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
                f'Spec - {self.__class__.__name__}: Compared {left} == {right}, use is operator'
                f'File {call_file_name}, line {call_line_num}.')
            '''

            return True
        return False

    """
    Discussion: this probably happens frequently in loops when comparing an object in a list with all other objects.
    Therefore this might be a common useless error.
    """

    def compared_with_itself(self, dyn_ast: str, iid: int, left: Any, right: Any) -> bool:
        if id(left) == id(right):
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
                f'Spec - {self.__class__.__name__}: Compared {left} with itself'
                f'File {call_file_name}, line {call_line_num}.')
            '''

            return True
        return False

    def compared_different_types(self, dyn_ast: str, iid: int, left: Any, right: Any, result: Any) -> bool:
        # we ignore float / int comparisons
        if (isinstance(left, type(0)) and isinstance(right, type(0.0))) or (
            isinstance(left, type(0.0)) and isinstance(right, type(0))
        ):
            return False

        type_left = type(left)
        type_right = type(right)

        # we have to check for isinstance here as well because subtypes can be used regarding the == operator
        if not result and not (isinstance(left, type_right) or isinstance(right, type_left)):
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
                f'Spec - {self.__class__.__name__}: Bad comparison: {type_left} == {type_right}'
                f'File {call_file_name}, line {call_line_num}.')
            '''

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
