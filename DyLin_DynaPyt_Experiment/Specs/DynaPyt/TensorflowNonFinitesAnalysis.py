from dynapyt.analyses.BaseAnalysis import BaseAnalysis

from typing import Any, Callable, Dict, Tuple
import tensorflow as tf
import warnings


class TensorflowNonFinitesAnalysis(BaseAnalysis):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event = {}
        self.unique_event = {}
        self.violation = 0
        self.unique_violation = 0
    
        tf.get_logger().setLevel("INFO")
        self.tracked_objects = {}
        self.total_tensors_investigated = 0

    def check_contains_nan_or_inf(self, tensor: tf.Tensor) -> bool:
        try:
            self.total_tensors_investigated = self.total_tensors_investigated + 1
            # checks if tensor contains NaN / inf / -inf by throwing an exception
            tf.debugging.check_numerics(tensor, "")
        except Exception as e:
            try:
                # Some uncommon exceptions for e can be thrown which do not
                # contain a message attribute as expected
                if "Tensor had" in e.message:
                    return True
            except Exception:
                return False
        return False

    def check_tf_issue_found(self, value: any) -> bool:
        if isinstance(value, tf.Tensor) and tf.is_tensor(value) and self.check_contains_nan_or_inf(value):
            return True
        return False

    def post_call(
        self,
        dyn_ast: str,
        iid: int,
        result: Any,
        function: Callable,
        pos_args: Tuple,
        kw_args: Dict,
    ) -> Any:
        # print(f"{self.analysis_name} post_call {iid}")
        if result is function:
            return
        args = list(kw_args.values() if not kw_args is None else []) + list(pos_args if not pos_args is None else [])
        no_nan_in_input = True

        for arg in args:
            if self.check_tf_issue_found(arg):
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
                    f'Spec - {self.__class__.__name__}: NaN in tensor input, result also contains NaN arg {arg}. '
                    f'File {call_file_name}, line {call_line_num}.')

                no_nan_in_input = False

        if self.check_tf_issue_found(result):
            if no_nan_in_input:
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
                    f'Spec - {self.__class__.__name__}: NaN in result tensor after applying function {function}. '
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
