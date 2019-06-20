from setuptools import setup, find_packages

setup(
    name='lib_bgp_data',
    packages=find_packages(),
    version='0.1.31',
    author='Justin Furuness',
    author_email='jfuruness@gmail.com',
    url='https://github.com/jfuruness/lib_bgp_data.git',
    download_url='https://github.com/jfuruness/lib_bgp_data.git',
    keywords=['Furuness', 'furuness', 'pypi', 'package'],  # arbitrary keywords
    install_requires=[
        'setuptools',
        'requests',
        'beautifulsoup4',
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
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': [
            'parse_bgpstream.com = lib_bgpstream_parser.__main__:main'
        ]},
)
####https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/!!!
#https://stackoverflow.com/questions/1321270/how-to-extend-distutils-with-a-simple-post-install-script/1321345#1321345
#https://stackoverflow.com/questions/14441955/how-to-perform-custom-build-steps-in-setup-py
#1/0 # RUN INSTALL SCRIPT HERE AND CHANGE DOCS!!!
