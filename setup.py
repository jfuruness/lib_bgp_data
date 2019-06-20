from setuptools import setup, find_packages

setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.1.29',
    author='Justin Furuness',
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_bgp_data.git',
    download_url='https://github.com/jfuruness/lib_bgp_data.git',
    keywords=['Furuness', 'furuness', 'pypi', 'package'],  # arbitrary keywords
    install_requires=[
        'setuptools',
        'requests',
        'beautifulsoup4',
        'fileinput',
        'flasgger',
        'Flask',
        'multiprocess',
        'pathos',
        'psycopg2',
        'Werkzeug'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Linux',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': [
            'parse_bgpstream.com = lib_bgpstream_parser.__main__:main'
        ]},
)

