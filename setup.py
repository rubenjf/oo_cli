from setuptools import setup

setup(name='oo_client',
      version='0.5',
      description='Client library for HPOO',
      author='Matthew Mead-Briggs',
      author_email='matthew@meadbriggs.co.uk',
      install_requires=['requests'],
      scripts=['bin/hpoo'],
      test_suite='tests',
      tests_require=['mock'],
      license='MIT',
      packages=['oo_client'],
      zip_safe=False)
