from setuptools import setup


setup(
    name='rsmarket',
    version='0.1.0',
    description='Runescape Market Utilities',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
        'Topic :: Utilities',
    ],
    author='xunoaib',
    author_email='xunoaib@gmail.com',
    license='MIT',
    packages=['rsmarket'],
    install_requires=['python-dateutil', 'requests', 'sqlalchemy', 'tabulate'],
    entry_points={
        'console_scripts': ['rsmarket=rsmarket.main:main'],
    },
    zip_safe=False
)
