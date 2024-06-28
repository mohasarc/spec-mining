from distutils.core import setup, Extension

module = Extension('customfloat', sources = ['customfloat.c'])

setup(name='CustomFloat',
      version='1.0',
      description='This module patches float().',
      ext_modules=[module])


# build with `python3 setup.py build_ext --inplace`
# then run any python script