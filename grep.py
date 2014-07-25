#Copyright 2014 Mark Santesson
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


from __future__ import with_statement
import glob
import logging
import mock
import os
import re
import stat
import sys
import unittest


''' I'm tired of not having grep. When I need it I never need it enough
that it is worth installing. So I'm going to rewrite it in python. I'll
build it up as I need more features. It need not be performant.
'''


def _process(options, args):
    '''Returns a list of results. Each result is a tuple of (filename,
    line index (starting at 0), and the line from the file that matched).
    '''
    if len(args) < 2:
        raise Exception('Did not provide enough arguments.')
    expr,fileargs = args[0],args[1:]

    search_re = re.compile( expr, re.IGNORECASE if options.ignore_case else 0 )
    results = list()
    already_hit = set()

    for arg in fileargs:
        # os.path.normpath can break working through symlinks. This just
        # converts all slashes to the correct os.sep.
        arg = arg.replace('/', os.sep).replace('\\',os.sep)

        direct_part,name_part = os.path.split(arg)

        for dir_name in glob.glob(direct_part):

            results += _process_recurse( options, search_re
                                       , dir_name, name_part
                                       , already_hit )

    return results


def _process_recurse(options, search_re, direct, name, already_hit):
    if (direct, name) in already_hit:
        return []
    already_hit.add( (direct, name) )

    results = list()
    entry = os.path.join(direct,name)
    filepaths = glob.glob(entry)
    for filepath in filepaths:
        if filepath in already_hit:
            continue
        already_hit.add(filepath)

        if options.verbose:
            print 'Checking {0}'.format(filepath)

        if os.stat(filepath).st_mode & stat.S_IFDIR:
            continue    # Silently ignore directories matched by regex.

        elif not os.access(filepath, os.R_OK):
            results.append( (filepath, -1, 'Error: File not readable',) )

        else:
            lines = open(filepath).readlines()
            for i,line in enumerate(lines):
                if search_re.search( line ):
                    results.append( (filepath, i, line,) )

    if options.recurse:
        files_here = os.listdir(direct or '.')
        for file_here in files_here:
            # Don't go through ., .., .git, &c.
            if file_here.startswith('.'):
                continue

            # If a directory was given, join that with the files here.
            if direct:
                file_here = os.path.join(direct, file_here)

            if os.path.isdir(file_here):
                res = _process_recurse( options, search_re
                                      , file_here, name
                                      , already_hit )
                results += res

    return results


def main():
    import optparse

    helptext='''\
%prog --help
%prog -u
%prog expr [options] glob1 [glob2...]
This is an approximation of grep, but written in Python so it can be
moved around.
'''

    parser = optparse.OptionParser(usage=helptext)

    parser.add_option( '-r', dest='recurse', action='store_true'
                     , default=False
                     , help='Search subdirectories. Remember to put any'\
                            ' wildcards in quotes so that they are not'
                            ' handled by the command line processor.' )
    parser.add_option( '-i', dest='ignore_case', action='store_true'
                     , default=False, help='Ignore case.' )
    parser.add_option( '-v', dest='verbose', action='store_true'
                     , default=False, help='Verbose mode.' )
    parser.add_option( '-u', dest='unittest', action='store_true'
                     , default=False, help='Run unit tests.' )

    options, args = parser.parse_args()
    if options.unittest:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
        unittest.TextTestRunner().run(suite)
    else:
        if len(args) < 2:
            print 'No argument or filenames provided. Use "--help" to get help.'
            sys.exit(1)

        results = _process(options, args)
        results.sort()

        print '\n'.join( [ '%s(%d): %s' % (f,i+1,l.strip())
                           for f,i,l in results ] )


class TestTesting(unittest.TestCase):

    @staticmethod
    def options(**kwargs):
        attribs = dict( recurse     = False
                      , ignore_case = False
                      , verbose     = False
                      )
        attribs.update(kwargs)
        return mock.Mock(**attribs)

    @staticmethod
    def search(search_string, files=None, options=None):
        if files is None:
            files = [ sys.modules[__name__].__file__ ]
        return _process( options or TestTesting.options()
                       , [ search_string ] + files)

    def test_contains_simple_string(self):
        search_string = r'xyzzy_1'
        # case sensitive:AIDUGNAIDUVBNUCNA
        res = self.search(search_string)
        self.assertTrue(res)
        self.assertEquals(1, len(res))
        self.assertEquals(sys.modules[__name__].__file__, res[0][0])
        self.assertEquals(int, type( res[0][1] ))  # Line of occurance is int
        self.assertIn(search_string, res[0][2])

    def test_not_contains(self):
        search_string = r'xyzzy_+2'   # not here because of +
        res = self.search(search_string)
        self.assertFalse(res)

    def test_ignore_case(self):
        # Match 1: xyzzy_3
        search_string = r'XYZZY_+3'    # "+" prevents finding itself
        res = self.search(search_string, options=self.options(ignore_case=True))
        self.assertEquals(1, len(res), 'Should be two results: {0}'.format(res))

    def test_recurse(self):
        search_string = r'xyzzy_4'
        res = self.search( search_string, ['../*.py']
                         , self.options(recurse=True) )
        self.assertTrue(res)
        self.assertEquals(1, len(res))
        fn = sys.modules[__name__].__file__.split(os.sep)
        fn = os.sep.join( ['..'] + fn[-2:] )
        self.assertEquals(fn, res[0][0])
        self.assertIn(search_string, res[0][2])

    def test_single_matches(self):
        search_string = r'xyzzy_5'
        res = self.search( search_string, ['../*.py','../*.py']
                         , self.options(recurse=True) )
        self.assertEquals(1, len(res), 'Failed detecting dir already done')

        res = self.search( search_string, ['../*.py', '../?*.py']
                         , self.options(recurse=True) )
        self.assertEquals(1, len(res), 'Failed detecting repeat of file')

    def test_globbing(self):
        search_string = r'xyzzy_6'
        direct,name = os.path.split(sys.modules[__name__].__file__)

        # Test glob in the directory, using ?.
        direct = direct[:-1] + '?'
        res = self.search( search_string, [os.path.join(direct,name)] )
        self.assertEquals(1, len(res))

        # Test glob in the directory, using *.
        direct = direct[:-1] + '*'
        res = self.search( search_string, [os.path.join(direct,name)] )
        self.assertEquals(1, len(res))

        # Clean up direct from our just completed tweaking.
        direct,name = os.path.split(sys.modules[__name__].__file__)

        # Test glob in the filename part.
        name = '*' + name[1:]
        res = self.search( search_string, [os.path.join(direct,name)] )
        self.assertEquals(1, len(res))

    def test_raise_when_no_files(self):
        with self.assertRaises(Exception):
            res = _process(None, [ 'dsaduinNosaidaDOA' ])


if __name__ == '__main__':
    main()

