from distutils.core import setup, Extension

module = Extension('customlist', sources = ['customlist.c'])

setup(name='CustomList',
      version='1.0',
      description='This module patches the list append method.',
      ext_modules=[module])


# build with `python3 setup.py build_ext --inplace`
# then run any python script