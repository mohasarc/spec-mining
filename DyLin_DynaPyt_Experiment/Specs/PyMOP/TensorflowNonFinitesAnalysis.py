from pythonmop import Spec, call, VIOLATION
import tensorflow as tf

import pythonmop.spec.spec as spec


tensor_creation_fns = [
    {'module': tf, 'fn_name': 'constant'},
    {'module': tf, 'fn_name': 'Variable'},
    {'module': tf, 'fn_name': 'ones'},
    {'module': tf, 'fn_name': 'zeros'},
    {'module': tf.random, 'fn_name': 'normal'},
    {'module': tf.random, 'fn_name': 'uniform'},
]

class TensorflowNonFinitesAnalysis(Spec):
    """
    Checks for NaNs, infs, and -infs in TensorFlow tensors, including SparseTensor and RaggedTensor.
    """

    def __init__(self):
        super().__init__()

        self.total_tensors_investigated = 0

        # Hook into Tensor creation
        for fn_to_instrument in tensor_creation_fns:
            @self.event_after(call(fn_to_instrument['module'], fn_to_instrument['fn_name']))
            def tensor_creation(**kw):
                return self.check_tf_issue_found(kw['return_val'])
        
        @self.event_after(call(tf.Tensor, '__init__'))
        def tensor_init(**kw):
            return self.check_tf_issue_found(kw['obj'])
    
        @self.event_after(call(tf.SparseTensor, '__init__'))
        def sparse_tensor_init(**kw):
            return self.check_tf_issue_found(kw['obj'])

        @self.event_after(call(tf.RaggedTensor, '__init__'))
        def ragged_tensor_init(**kw):
            return self.check_tf_issue_found(kw['obj'])

        # Hook into Tensor operations
        @self.event_after(call(tf.Tensor, r'(__add__|__sub__|__mul__|__truediv__|__matmul__|__pow__|__mod__|__floordiv__)'))
        def tensor_op(**kw):
            return self.check_tf_issue_found(kw['return_val'])

        # Hook into SparseTensor and RaggedTensor methods
        @self.event_after(call(tf.SparseTensor, r'(__add__|__sub__|__mul__|__truediv__|__matmul__|__pow__|__mod__|__floordiv__)'))
        def sparse_tensor_op(**kw):
            return self.check_tf_issue_found(kw['return_val'])

        @self.event_after(call(tf.RaggedTensor, r'(__add__|__sub__|__mul__|__truediv__|__matmul__|__pow__|__mod__|__floordiv__)'))
        def ragged_tensor_op(**kw):
            return self.check_tf_issue_found(kw['return_val'])


    # Copied as is from https://github.com/sola-st/DyLin/blob/820506e532000edaa76f22f55ba94323006b2405/src/dylin/analyses/TensorflowNonFinitesAnalysis.py#L14
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
        # print('checking', value, 'which is a tensor?', tf.is_tensor(value))
        if tf.is_tensor(value) and self.check_contains_nan_or_inf(value):
            return VIOLATION

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: Non-finite value detected in tensor. '
            f'File {call_file_name}, line {call_line_num}.')
# =========================================================================

'''
spec_instance = TensorflowNonFinitesAnalysis()
spec_instance.create_monitor("D")


# Test cases
a = tf.constant([float("nan")])  # Should trigger
b = tf.Variable([float("inf")])  # Should trigger
c = tf.ones((2, 2)) / tf.constant([0.0])  # Should trigger
d = tf.zeros((2, 2)) + tf.constant([float("-inf")])  # Should trigger

# SparseTensor doesn't
# work (tf.debugging.check_numeric function doesn't throw the expected
# exception that indicates the usage of nan or inf)
e = tf.SparseTensor(indices=[[0, 0], [1, 2]], values=[float("nan"), 1.0], dense_shape=[2, 3])  # Should trigger [For some reason it doesn't work]

f = tf.RaggedTensor.from_row_lengths([float("inf"), 1.0, 2.0], [2, 1])  # Should trigger
'''