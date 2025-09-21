# ============================== Define spec ==============================
from pythonmop import Spec, call, getStackTrace, parseStackTrace, End
from pythonmop.statistics import StatisticsSingleton

import builtins


class MonitoredFile():
    def __init__(self, originalFile):
        self.originalFile = originalFile

    def open(self, file, stackTrace):
        pass

    def close(self, *args, **kwargs):
        pass


# ========== Override builtins open =============
# These are used to prevent infinite recursion
# when the monitored method is used within our
# event handling implementation
alreadyWithinOpen = False
alreadyWithinClose = False

originalOpen = builtins.open

def customOpen(*args, **kwargs):
    global alreadyWithinOpen
    if alreadyWithinOpen:
        return originalOpen(*args, **kwargs)

    originalFile = originalOpen(*args, **kwargs)
    monitoredFile = MonitoredFile(originalFile)
    originalClose = originalFile.close

    # find the path of the file calling this function and the line
    stackTrace = parseStackTrace(getStackTrace())

    if '_pytest/logging.py' not in stackTrace and 'monitor/monitor_a.py' not in stackTrace:
        alreadyWithinOpen = True
        monitoredFile.open(originalFile, stackTrace)
        alreadyWithinOpen = False

    def customClose(*args, **kwargs):
        global alreadyWithinClose
        if alreadyWithinClose:
            return originalClose(*args, **kwargs)
        
        alreadyWithinClose = True
        monitoredFile.close(*args, **kwargs)
        alreadyWithinClose = False
        return originalClose(*args, **kwargs)

    originalFile.close = customClose

    return originalFile

builtins.open = customOpen


# =================================================
class FileClosedAnalysis(Spec):
    """
    TODO: Add description here.
    """
    def __init__(self):
        self.opened = {}
        super().__init__()

        # open method
        @self.event_before(call(MonitoredFile, 'open'))
        def open(**kw):
            file = kw['args'][1]
            self.opened[file] = {
                                    'filename': kw['call_file_name'],
                                    'lineno': kw['call_line_num']
                                }

        # close method
        @self.event_before(call(MonitoredFile, 'close'))
        def close(**kw):
            file = kw['obj'].originalFile

            if file in self.opened:
                self.opened.pop(file)
        
        @self.event_after(call(End, 'end_execution'))
        def end(**kw):
            if len(self.opened) > 0:
                for file in self.opened:
                    # Get the custom message
                    custom_message = f'Spec - {self.__class__.__name__}: You forgot to close {file} at {self.opened[file]["filename"]}, {self.opened[file]["lineno"]}.'

                    # Print the custom message
                    print(custom_message)

                    # Add the violation into the statistics.
                    StatisticsSingleton().add_violation(self.__class__.__name__,
                                                        f'last event: {None}, param: {None}, '
                                                        f'message: {custom_message}, '
                                                        f'file_name: {self.opened[file]["filename"]}, line_num: {self.opened[file]["lineno"]}')

# =========================================================================

'''
spec_in = File_MustClose()
spec_in.create_monitor("File_MustClose")

t = open("test.txt", "w")
# forgot to close the file t

with open("test2.txt", "w") as t1:
    # Any code that uses the resource
    pass
# exiting the block automatically closes the other file t1

spec_in.end()
'''