import pymopeventemitter
import time
import my_python_functions

emitter = pymopeventemitter.PyMopEventEmitter()
emitter.subscribe("hello", lambda: print("Hello event triggered"))
# emitter.set_global_emitter(emitter)

emitter.emit("hello")


def main():
    a = []
    print('--------------- first line a ---------------')
    a.append('--------------- first line a ---------------')
    a.append(1)
    a.append(2)
    a.append(3)
    a.append('--------------- last line a ---------------')

    b = []
    b.append('--------------- first line b ---------------')
    b.append(4)
    b.append({'a': 1, 'b': 2})
    b.append(5)
    b.append('--------------- last line b ---------------')


def delayed_function(): 
    print("This message will be printed after 3 seconds")
    c = []
    c.append('--------------- first line c ---------------')
    c.append(6)
    c.append(7)
    c.append(8)
    c.append('--------------- last line c ---------------')

if __name__ == '__main__':
    main()
 
    time.sleep(30) 
    delayed_function()