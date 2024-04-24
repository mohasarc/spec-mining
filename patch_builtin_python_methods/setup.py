from distutils.core import setup, Extension

module = Extension('pymopeventemitter', sources = ['pymopeventemitter.c'])

setup(name='PyMopEventEmitter',
      version='1.0',
      description='Python C API event emitter example',
      ext_modules=[module])