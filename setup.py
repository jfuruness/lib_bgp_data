from setuptools import setup, find_packages

def get_parsers():
    """Note: I could try to import this function but...

    Then it gets really messy, and is not longer useful.
    So we must simple write a new one here. Oh well.
    """

    return ["mrt_parser"]

def _get_console_scripts():
    """Returns all console scripts"""

    return [f'{name} = lib_bgp_data.__main__:main' for name in get_parsers()]

setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.2.4',
    authors=['Justin Furuness', 'Matt Jaccino'],
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_bgp_data.git',
    download_url='https://github.com/jfuruness/lib_bgp_data.git',
    keywords=['Furuness', 'BGP', 'ROA', 'MRT', 'RPKI', 'ROV', 'ROV++'],
    install_requires=[
        'wheel',
        'setuptools',
        'validators>=0.14.1',
        'tqdm>=4.40.2',
        'pytest==4.6.6',
        'psutil==5.6.7',
        'Flask>=1.1.1',
        'requests>=2.22.0',
        'pathos>=0.2.5',
        'flasgger>=0.9.3',
        'multiprocess>=0.70.9',
        'psycopg2_binary>=2.8.4',
        'Werkzeug>=0.16.0',
        'pytz>=2019.3',
        'beautifulsoup4>=4.8.1',
        'psycopg2>=2.8.4',
        'matplotlib',
        'jsonschema==2.6.0'  # required for flasgger
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': _get_console_scripts()},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
####https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/!!!
#https://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script/1321345#1321345
#https://stackoverflow.com/questions/14441955/how-to-perform-custom-build-steps-in-setup-py
#1/0 # RUN INSTALL SCRIPT HERE AND CHANGE DOCS!!!
