from setuptools import setup, find_packages


def _get_console_scripts():
    """Returns all console scripts, needs docs"""

    console_scripts = []
    permutations_funcs = [_roas_collector_permutations,
                          _relationships_parser_permutations,
                          _mrt_parser_permutations]
    for func in permutations_funcs:
        permutations, module_name = func()
        for permutation in permutations:
            append_str = '= lib_bgp_data.{}.__main__:main'.format(module_name)
            console_scripts.append(permutation + append_str)
    return console_scripts


def _roas_collector_permutations():
    """Gets every possible combination of arg for useability"""

    possible_permutations = []
    for j in ["ROA", "roa"]:
        for k in ["S", "s", ""]:
            # I know l is bad but this function sucks anways
            for l in ["-", "_", " "]:
                for m in ["Collector", "COLLECTOR", "collector",
                          "Parser", "parser", "PARSER"]:
                    possible_permutations.append(j + k + l + m)
    # Returns the permutations and the package name
    return possible_permutations, "roas_collector"


def _relationships_parser_permutations():
    """Gets every possible combination of arg for usability"""

    possible_permutations = []
    for i in ["Relationship", "relationship", "Rel", "rel"]:
        for j in ["S", "s", ""]:
            for k in ["_", "", "-"]:
                for l in ["Parser", "parser", "Par", "par"]:
                    possible_permutations.append(i + j + k + l)
    return possible_permutations, "relationships_parser"


def _mrt_parser_permutations():
    """Gets every possible combination pf arg for usability"""

    possible_permutations = []
    for j in ["MRT", "mrt"]:
        for k in ["S", "s", ""]:
            for l in ["-", "", "_"]:
                for m in ["Parser", "parser", "par", "Par"]:
                    possible_permutations.append(j + k + l + m)
    return possible_permutations, "mrt_parser"


setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.2.4',
    author='Justin Furuness and Matt Jaccino',
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
