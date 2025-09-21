# ============================== Define spec ==============================
from pythonmop import Spec, call, getKwOrPosArg, VIOLATION
from socket import socket

class socket_socket_settimeout(Spec):
    """
    timeout must not be a negative number
    src: https://docs.python.org/3/library/socket.html#socket.socket.settimeout
    """

    def __init__(self):
        super().__init__()


        @self.event_before(call(socket, 'settimeout'))
        def run(**kw):
            timeout = getKwOrPosArg('value', 1, kw)

            # must not a negative number
            if timeout is not None and timeout < 0:
                return {'verdict': VIOLATION, 
                        'custom_message': f"Timeout must not be a negative number at {kw['call_file_name']}, {kw['call_line_num']}.",
                        'filename': kw['call_file_name'],
                        'lineno': kw['call_line_num']}

    def match(self, call_file_name, call_line_num):
        # TODO:
        print(
            f'Spec - {self.__class__.__name__}: Timeout must not be negative. file {call_file_name}, line {call_line_num}.')
# =========================================================================