from distutils.core import setup, Extension
 
module1 = Extension('hdhr', sources = ['hdhrmodule.c'], libraries=['hdhomerun'])
 
setup (name = 'hdhr',
        version = '1.0',
        description = 'This is a demo package',
        ext_modules = [module1])
