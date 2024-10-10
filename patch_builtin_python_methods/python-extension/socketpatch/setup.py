from distutils.core import setup, Extension

module = Extension('customsettimeout', sources = ['customsettimeout.c'])

setup(name='customsettimeout',
      version='1.0',
      description='This module patches int().',
      ext_modules=[module])


# build with `python3 setup.py build_ext --inplace`
# then run any python script