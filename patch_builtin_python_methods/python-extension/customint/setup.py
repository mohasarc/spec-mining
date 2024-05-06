from distutils.core import setup, Extension

module = Extension('customint', sources = ['customint.c'])

setup(name='CustomInt',
      version='1.0',
      description='This module patches the int bit_length method.',
      ext_modules=[module])


# build with `python3 setup.py build_ext --inplace`
# then run any python script