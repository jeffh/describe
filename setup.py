from setuptools import setup, find_packages

execfile('describe/meta.py')

setup(
    name='describe',
    version=__version__,
    description='An experimental behavioral framework.',
    long_description=open('README.rst').read(),
    author=__author__,
    author_email=__author_email__,
    url='http://github.com/jeffh/describe/',
    install_requires=[],
    entry_points = {
        #'nose.plugins.0.10': ['describe = describe.nose_plugin:SpecPlugin'],
        'console_scripts': ['describe = describe:main'],
    },
    test_suite = 'tests.run',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
    ],
)
