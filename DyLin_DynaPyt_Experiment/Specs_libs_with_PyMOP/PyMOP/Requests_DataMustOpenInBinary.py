# ============================== Define spec ==============================
from pythonmop import Spec, call, VIOLATION
import requests


class Requests_DataMustOpenInBinary(Spec):
    """
    It is strongly recommended that you open files in binary mode. This is because Requests may attempt to provide
    the Content-Length header for you, and if it does this value will be set to the number of bytes in the file.
    Errors may occur if you open the file in text mode."""

    def __init__(self):
        super().__init__()

        def do_verify(**kw):
            kwargs = kw['kwargs']
            kwords = ['data', 'files']
            for k in kwords:
                if k in kwargs:
                    data = kwargs[k]
                    if hasattr(data, 'read') and hasattr(data, 'mode') and 'b' not in data.mode:
                        return {'verdict': VIOLATION, 
                                'custom_message': f"It is strongly recommended that you open files in binary mode. This is because Requests may attempt to provide the Content-Length header for you, and if it does this value will be set to the number of bytes in the file. Errors may occur if you open the file in text mode at {kw['call_file_name']}, {kw['call_line_num']}.",
                                'filename': kw['call_file_name'],
                                'lineno': kw['call_line_num']}

        @self.event_before(call(requests, 'post'))
        def test_verify(**kw):
            return do_verify(**kw)

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: It is strongly recommended that you open files in binary mode. This '
            f'is because Requests may attempt to provide the Content-Length header for you, and if it does this value '
            f'will be set to the number of bytes in the file. Errors may occur if you open the file in text mode. in '
            f'{call_file_name} at line {call_line_num}')


# =========================================================================

'''
spec_instance = Requests_DataMustOpenInBinary()
spec_instance.create_monitor("A")
with open('test.txt', 'r') as f:
    s = requests.post('https://github.com/', data=f)

with open('test.txt', 'r') as f:
    session = Session()
    s = session.post('https://github.com/', data=f)


spec_instance.get_monitor().refresh_monitor()
'''
