from setuptools import setup, find_packages

__version__, __author__, __author_email__ = "0.1.2", "Jeff Hui", "contrib@jeffhui.net"

setup(
    name='describe',
    version=__version__,
    description='An experimental behavioral framework inspired from rspec.',
    long_description=open('README.rst').read(),
    author=__author__,
    author_email=__author_email__,
    url='http://github.com/jeffh/describe/',
    # The runner hasn't been extensively tested.
    install_requires=[
        'nose',
        'mock',
    ],
    entry_points = {
        'nose.plugins.0.10': ['describe = describe.nose_plugin:SpecPlugin'],
        #'console_scripts': ['describe = describe:main'],
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
