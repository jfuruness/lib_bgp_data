from setuptools import setup, find_packages

setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.1.2',
    author='Justin Furuness',
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_bgp_data.git',
    download_url='https://github.com/jfuruness/lib_bgp_data.git',
    keywords=['Furuness', 'furuness', 'pypi', 'package'],  # arbitrary keywords
    install_requires=[
        'pybgpstream',
        'setuptools',
        'psycopg2',
        'requests',
        'bs4'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': [
            'parse_bgpstream.com = lib_bgpstream_parser.__main__:main'
        ]},
)

