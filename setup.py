from setuptools import setup, find_packages

def _get_console_scripts():

    console_scripts = []
    console_scripts.extend(_get_roas_console_scripts())
    return console_scripts

def _get_roas_console_scripts():
    console_scripts = []
    for permutation in _roas_collector_permutations():
        script = permutation + '= lib_bgp_data.roas_collector.__main__:main'
        console_scripts.append(script)
    return console_scripts

def _roas_collector_permutations():
    """Gets every possible combination of arg for useability"""

    possible_permutations = []
    for j in ["ROA", "roa"]:
        for k in ["S", "s"]:
            # I know l is bad but this function sucks anways
            for l in ["-", "_", " "]:
                for m in ["Collector", "COLLECTOR", "collector",
                          "Parser", "parser", "PARSER"]:
                    possible_permutations.append(j + k + l + m)
    return possible_permutations



setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.2.4',
    author='Justin Furuness',
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_bgp_data.git',
    download_url='https://github.com/jfuruness/lib_bgp_data.git',
    keywords=['Furuness', 'BGP', 'ROAs', 'MRTs', 'RPKI', 'ROV', 'ROV++'],  # arbitrary keywords
    install_requires=[
        'wheel',
        'setuptools',
        'requests',
        'beautifulsoup4',
        'flasgger',
        'Flask',
        'multiprocess',
        'pathos',
        'psutil',
        'psycopg2-binary',
        'pytest',
        'Werkzeug'
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': [*_get_console_scripts()]},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)
####https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/!!!
#https://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script/1321345#1321345
#https://stackoverflow.com/questions/14441955/how-to-perform-custom-build-steps-in-setup-py
#1/0 # RUN INSTALL SCRIPT HERE AND CHANGE DOCS!!!
