from pythonmop.builtin_instrumentation import class_creation_listener
from pythonmop import Spec, call, TRUE_EVENT, FALSE_EVENT
import pythonmop.spec.spec as spec
import inspect
import time

# spec.DONT_MONITOR_PYTHONMOP = False

def get_all_subclasses(cls):
    all_subclasses = []

    try:
        subclasses = cls.__subclasses__()
    except:
        return all_subclasses

    for subclass in subclasses:
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses

class InefficientTruthCheck(Spec):
    """
    Detects inefficient __bool__ or __len__ checks.
    """
    THRESHOLD_TIME = 10000000  # 10 ms

    def __init__(self):
        super().__init__()

        self.tracked_calls = {} # { object_id+method_name: { start_time } }

        # for current_class in get_all_subclasses(object):
        #     try:
        #         current_class.__PYMOP_IMMUTABLE_TEST__ = True
        #         inspect.getmembers(current_class)
        #     except Exception as e:
        #         # Skip classes that can't be instrumented
        #         continue

        #     @self.event_before(call(current_class, r'(__bool__|__len__)'))
        #     def bool_or_len_start(**kw):
        #         return self.handle_before_event(kw)
            
        #     @self.event_after(call(current_class, r'(__bool__|__len__)'))
        #     def bool_or_len_end(**kw):
        #         return self.handle_after_event(kw)

        @self.event_before(call(object, r'(__bool__|__len__)'))
        def bool_or_len_start(**kw):
            return self.handle_before_event(kw)
        
        @self.event_after(call(object, r'(__bool__|__len__)'))
        def bool_or_len_end(**kw):
            return self.handle_after_event(kw)

        def on_new_class(cls):
            @self.event_before(call(cls, r'(__bool__|__len__)'))
            def bool_or_len_start(**kw):
                return self.handle_before_event(kw)
            
            @self.event_after(call(cls, r'(__bool__|__len__)'))
            def bool_or_len_end(**kw):
                return self.handle_after_event(kw)

        class_creation_listener.on_class_creation(on_new_class)

    def handle_before_event(self, kw):
        obj = kw['obj']
        func_name = kw['func_name']
        self.record_start_time(obj, func_name)
        return FALSE_EVENT

    def handle_after_event(self, kw):
        obj = kw['obj']
        func_name = kw['func_name']

        if self.check_inefficient_check(obj, func_name):
            return TRUE_EVENT
        return FALSE_EVENT

    def record_start_time(self, obj, func_name):
        self.tracked_calls[f'{id(obj)}:{func_name}'] = time.time_ns()

    def check_inefficient_check(self, obj, func_name):
        start_time = self.tracked_calls[f'{id(obj)}:{func_name}']
        del self.tracked_calls[f'{id(obj)}:{func_name}']
        end_time = time.time_ns()

        if end_time - start_time > self.THRESHOLD_TIME:
            return True
        return False

    ere = '(bool_or_len_start|bool_or_len_end)+'
    creation_events = ['bool_or_len_start', 'bool_or_len_end']

    def match(self, call_file_name, call_line_num):
        print(
            f'Spec - {self.__class__.__name__}: too slow __bool__ or __len__ check taking over 10ms. file: {call_file_name}:{call_line_num}')

'''
the_spec = InefficientTruthCheck()
the_spec.create_monitor('D')

class A():
    def __bool__(self):
        for i in range(10000000):
            pass
        return False
    
    def __len__(self):
        return 0

a = A()

bool(a) # Too slow 
len(a) # Fine
'''
