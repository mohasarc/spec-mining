from distutils.core import setup, Extension

module = Extension('customlistsort', sources = ['customlistsort.c'])

setup(name='CustomListsort',
      version='1.0',
      description='This module patches list.sort().',
      ext_modules=[module])


# build with `python3 setup.py build_ext --inplace`
# then run any python script