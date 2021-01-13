#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module contains class MRT_Installer

The purpose of this class is to Install dependencies required for the
MRT_Parser and it's unit tests. That includes bgpscanner (and all of it's
dependencies) and bgpdump. See each function for specifics on installation.
"""

__authors__ = ["Justin Furuness"]
__credits__ = ["Justin Furuness"]
__Lisence__ = "BSD"
__maintainer__ = "Justin Furuness"
__email__ = "jfuruness@gmail.com"
__status__ = "Development"

from ..utils import utils


class MRT_Installer:
    """This class installs all dependencies needed for MRT_Parser.

    In depth explanation at the top of module.
    """

    __slots__ = []

    def __init__(self, **kwargs):
        """Initializes logger and path variables."""

        config_logging(kwargs.get("stream_level"), kwargs.get("section"))

    def install_dependencies(self):
        """Downloads all dependencies required

        That includes, bgpscanner, and bgpdump,
        and of course their dependencies.
        """

        self._install_bgpscanner()
        self._install_bgpdump()

    @utils.delete_files(["bgpscanner/", "delete_me/"])
    def _install_bgpscanner(self):
        """Installs bgpscanner to /usr/bin/bgpscanner.

        Also installs lzma-dev, which apparently is necessary.
        """

        # Installs all deps we can do with apt
        self._install_bgpscanner_deps()
        # Downloads bgpscanner and modifies it for malformed announcements
        # Which we need because they exist in the real world
        self._download_and_modify_bgpscanner()
        # Builds bgpscanner and moves it to desired location
        self._build_bgpscanner()
        # Installs lib_isocore which bgpscanner needs to run
        self._install_lib_isocore()

    @utils.delete_files("bgpdump/")
    def _install_bgpdump(self):
        """Installs bgpdump and all dependencies"""

        cmds = ["git clone https://github.com/RIPE-NCC/bgpdump.git",
               "cd bgpdump/",
               "sh ./bootstrap.sh",
               "./bgpdump -T",
               "sudo cp bgpdump /usr/bin/bgpdump" ]
        utils.run_cmds(cmds)
        utils.run_cmds("sudo cp bgpdump /usr/local/bin/bgpdump")

###################################
### bgpscanner Helper Functions ###
###################################

    def _install_bgpscanner_deps(self):
        """Installs all bgpscanner dependencies"""

        self._install_lzma_dev()
        cmds = ["sudo apt -y install meson",
                "sudo apt -y install zlib1g",
                "sudo apt -y install zlib1g-dev",
                "sudo apt-get -y install libbz2-dev",
                "sudo apt-get -y install liblzma-dev",
                "sudo apt-get -y install liblz4-dev",
                "sudo apt-get -y install ninja-build",
                "pip3 install --user meson",
                "sudo apt-get -y install cmake"]
        utils.run_cmds(cmds)

    @utils.delete_files("lzma-dev/")
    def _install_lzma_dev(self):
        """Installs lzma-dev, needed for bgpscanner"""

        

        cmds = ["mkdir lzma-dev",
                "cd lzma-dev/",
                "wget https://tukaani.org/xz/xz-5.2.4.tar.gz",
                "tar -xvf xz-5.2.4.tar.gz",
                "cd xz-5.2.4/",
                "./configure ",
                "make",
                "sudo make install"]

        utils.run_cmds(cmds)

    def _download_and_modify_bgpscanner(self):
        """Downloads bgpscanner and modifies it.

        The reason it modifies it is because it used to reject
        announcements with malformed attributes. However, bgpdump
        does not, and because we know that they are in actual RIBs
        of ASes, it makes sense to include them in our simulation.
        """

        utils.run_cmds("git clone https://gitlab.com/Isolario/bgpscanner.git")
        # If this line is not changed it remove improper configurations.
        # We want to keep these because they are included in the monitors
        # Announcements, so they clearly are propogated throughout the
        # internet.
        path = "bgpscanner/src/mrtdataread.c"
        prepend = '                if ('
        replace = 'rib->peer->as_size == sizeof(uint32_t))'
        replace_with = 'true)'
        utils.replace_line(path, prepend, replace, replace_with)

    def _build_bgpscanner(self):
        """Builds bgpscanner.

        For some reason, meson refuses to be installed in a good location
        so we need to pip install it in our python env and run from there.
        """

        cmds = ["python3 -m venv delete_me",
                "delete_me/bin/pip3 install wheel",
                "delete_me/bin/pip3 install meson",
                "cd bgpscanner",
                "mkdir build && cd build",
                "../../delete_me/bin/meson ..",
                "cd ../../",
                "cd bgpscanner/build",
                "sudo ninja install",
                "sudo ldconfig",
                "cd ../../",
                "cp bgpscanner/build/bgpscanner /usr/bin/bgpscanner"]
        utils.run_cmds(cmds)

        # Our second server runs from here, so we need to:
        utils.run_cmds(("cp bgpscanner/build/bgpscanner "
                        "/usr/local/bin/bgpscanner"))

    def _install_lib_isocore(self):
        """This installs lib_isocore.

        bgpscanner needs this to run, and apparently it does not install
        properly by default so we need to build it and move it.
        """

        cmds = ["cd bgpscanner/subprojects/",
                "git clone https://gitlab.com/Isolario/isocore.git",
                "cd isocore",
                "mkdir build && cd build",
                "../../../../delete_me/bin/meson ..",
                "cd ../../",
                "cd isocore/build",
                "sudo ninja install",
                "sudo ldconfig",
                "cd ../../",
                "cp isocore/build/libisocore.so /usr/lib/libisocore.so"]
        utils.run_cmds(cmds)
