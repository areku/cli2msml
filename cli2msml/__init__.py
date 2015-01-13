# Copyright (C) 2014 Alexander Weigl
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Alexander Weigl'
__version__ = '0.1-alpha'

from .log import *
import argparse
import os
from path import path
from cli2msml.create import CreateCLI, AbortOperationError, set_config, MsmlArgument

#region command line
def create_argument_parser():
    p = argparse.ArgumentParser()
    p.add_argument("executable", metavar="EXECUTABLE", nargs='*', help="CLI executable")
    p.add_argument("-o", "--output-dir", metavar="FOLDER", action="store", dest="output_dir", help="output folder",
                   default="alphabet/")
    p.add_argument("-d", "--doc-output-dir",
                   metavar="FOLDER", action="store",
                   dest="doc_dir", help="output folder for documentation",
                   default="docs/")

    p.add_argument("-v", '--verbose',
                        default=2,
                        dest="verbosity", action="count",
                        help="select the verbosity of this program")
    return p

import cli2msml.log as log

def load_config(filename = "c2mconf.py"):
    filename = path(filename)
    if filename.exists():
        g = {"Slot" : MsmlArgument}
        l = {}
        execfile(filename, g, l)
        log.info("Load configuration: %s", filename.abspath())
        return l
    else:
        log.info("Configuration not found: %s", filename.abspath())
        return None

def main():
    args = create_argument_parser().parse_args()

    log.set_verbosity(
        "WARNING" if args.verbosity == 1 else
        "INFO" if args.verbosity == 2 else
        "DEBUG" if args.verbosity == 3 else
        "ERROR")

    if  os.path.isdir(args.executable[0]):
        binfolder = path(args.executable[0])
        print("ALL MODE ON, take every executable in %s" % binfolder.abspath())
        executables = filter(lambda fpath: os.access(fpath, os.X_OK),
                             binfolder.walkfiles("*",errors="ignore"))
    else:
        executables = args.executable


    set_config(load_config())

    path(args.output_dir).makedirs_p()
    path(args.doc_dir).makedirs_p()

    for executable in executables:
        try:
            create = CreateCLI(executable)
            create.do()
            fil = "%s/%s.msml.xml" % (args.output_dir, create.name)
            info("Write %s to %s", executable, fil)
            with open(fil, 'w') as fp:
                fp.write(create.msml)


            fil = "%s/%s.rst" % (args.doc_dir, create.name)
            info("Write %s to %s" , executable, fil)
            with open(fil, 'w') as fp:
                fp.write(create.rst)

            fil = "%s/%s.md" % (args.doc_dir, create.name)
            info("Write %s to %s" , executable, fil)
            with open(fil, 'w') as fp:
                fp.write(create.markdown)

        except AbortOperationError:
            pass

#endregion