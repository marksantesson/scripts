
#Copyright 2012,2014 Mark Santesson
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# To make this run more easily in windows, add the file into the path
# and make sure that *.py files are associated with python:
#   C:\>assoc .PY=Python.File
#   C:\>ftype Python.File=c:\Python27\Python.exe "%1" %*


import sys
import time
import re
import stat
import os
import glob
import operator
import optparse


def globAndMaybeRecurse(globs):
    walks = os.walk(os.getcwd(), followlinks=True)
    dirs_here = [ x[0] for x in walks ]
    ret = list()
    for d in dirs_here:
        gs = [ os.path.join(d, g) for g in globs ]
        ret.extend( sum([ glob.glob( g ) for g in gs ], []) )

    return ret


if __name__ == "__main__":

    parser = optparse.OptionParser (
                        usage = '%prog -c <command> files ...',
                        description = 'Repeatedly run a command whenever any one of a list of files changes.')
    parser.add_option( '-c', '--command', dest='command', type="string"
                     , help='Specify command to run when a change is detected')
    parser.add_option( '-r', '--recurse', dest='recurse', action='store_true'
                     , default=False, help='Apply glob to subdirectories, too.')
    options, args = parser.parse_args()


    if not args:
        print '\n' + os.path.basename( sys.argv[0] ) + ' requires some files to monitor.'
        sys.exit(1)

    if not options.command:
        print '\nError: A command to run is required.'
        sys.exit(1)


    file_times = dict()
    globbed = sum( [ glob.glob(x) for x in args ], [] )

    if options.recurse:
        local_args = [ x for x in args if '/' not in x and '\\' not in x ]
        globbed.extend( globAndMaybeRecurse( local_args ) )

    for x in globbed:
        file_times[x] = 0.0

    while True:
        rerun = False

        for f in file_times.keys():
            attempts_left = 5
            t = None
            while attempts_left and t == None:
                try:
                    t = os.stat(f)[ stat.ST_MTIME ]
                except WindowsError, e:
                    time.sleep(0.1)
                    attempts_left -= 1

            if t > file_times[f]:
                rerun = True
                file_times[f] = t

        if rerun:
            print time.strftime('\n\n--- Rerunning at %H:%M:%S :') + repr(options.command)
            ret = os.system( options.command )

            if ret:
                print '\n\n--- ERRORED %r' % (ret,) + time.strftime(' at %H:%M:%S.')

            else:
                print time.strftime('\n\n--- Done at %H:%M:%S.')

        else:
            time.sleep(0.5)

else:
    raise Exception( 'This module is not meant to be imported.' )

