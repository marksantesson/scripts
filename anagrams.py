#!/usr/bin/python

#Copyright 2011, 2012 Mark Santesson
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



'''
Anagram generator. Use prime numbers to represent the phrase given.
Each letter has a unique prime number. A phrase's signature is
the product of all the prime numbers assigned to the component
letters.  The signatures for any set of phrases which are anagrams
of each other will all be the same number.
By Mark Santesson.
'''

import time, os, sys, collections


timings = []
last_time = time.clock()

def elapsedTime():
    '''Return the number of seconds that has passed since the last time this
    function was called. The first time it is called it will return the time
    since the function was defined.'''
    global last_time
    this_time = time.clock()
    elap_time = this_time - last_time
    last_time = this_time
    return elap_time

def addTiming(desc):
    timings.append( ( elapsedTime(), desc, ) )



def nextprime(x):
    """Quick prime number calculator. Pass in a number and it will return
    the smallest prime strictly larger than the input. It is very
    inefficient."""

    # Create a function which returns the next prime larger than the
    # passed value. A faster way to do this is to keep track of all
    # primes seen so far and then start trying primes incrementally
    # higher than that, dividing only by the other primes already
    # found. You can also stop at sqrt(x). I'm only going to generate
    # 26 of them, so this easy method is fine.

    while True:    # On the theory that there are an infinite number of primes...
        x += 1
        for pot_fac in range(2,x):    # Not even using the sqrt(x) or even numbers optimizations!
            if x % pot_fac == 0:
                break
        else:
            return x



def prime_generator():
    '''Returns a generator that produces the next largest prime as
    compared to the one returned from this function the last time
    it was called. The first time it is called it will return 2.'''
    lastprime = 1
    while True:
        lastprime = nextprime(lastprime)
        yield lastprime






class AnagramGenerator:
    '''The AnagramGenerator class produces all anagram combinations
    that are possible from the input phrase using the given dictionary.
    If no dictionary is given to the constructor (as a filename)
    then it assumes "words" is the filename.'''
    def __init__(self, dictionary_filename='words'):
        '''Make a AnagramGenerator object. There is no way to
        switch dictionaries; create a new instance instead.'''
        self.dictionary_filename = dictionary_filename
        self.__loadDictionary()

    def __getPrime(self, c):
        '''Returns the prime number that represents the passed
        in character. The character must be lower case.'''
        # assert c==c.lower()
        return self.chars_list[ ord(c) - ord('a') ]

    def __getSignature(self, s):
        '''Returns the integer that represents the characters in
        a string.  The integer is the product of the prime number
        representation of each character in the string.'''
        s = s.lower()
        sig = reduce(lambda x,y: x * self.__getPrime(y),
            [ch for ch in s if ord('a') <= ord(ch) <= ord('z')], 1)
        assert sig >= 1, repr( ('Product of primes produced non-positive number',s, sig, [ (z,self.__getPrime(z)) for z in s if ord('a') <= ord(z) <= ord('z') ]) )
        return sig

    def __loadDictionary(self):
        '''Load a dictionary from the given input file.  The file
        should have one word per line.'''

        addTiming('Start of loading dictionary from "%s"' % (self.dictionary_filename,))

        # Count chars in the dictionary. Create a dict of lower
        # case character to the number of instances found in the
        # words dictionary. It might be useful to break this
        # function into two parts to enable custom dictionaries
        # passed in as a list/string instead of just specifying
        # a dictionary filename. However, since I'm testing
        # the performance of this script, I need to combine the
        # counting and the line loading to prevent a second
        # loop. There are ways around that, but it isn't a
        # focus for now. If loading from something other than
        # a dictionary file is needed then this is the place
        # to make that change.

        all_lines = list()
        counts = dict([ (chr(x),0) for x in range(ord('a'), ord('z')+1) ])
        for line in open( self.dictionary_filename ).readlines():
            all_lines.append(line.strip())
            for c in line.lower():
                if ord('a') <= ord(c) <= ord('z'):
                    counts[ c ] += 1


        # Construct a dict mapping from lower case character to the
        # prime number for it. Initialize it in the order of most
        # used character first, so that the letters most frequently
        # used get lower numbers in the hopes that the products
        # will be smaller numbers.

        primes = prime_generator() # get the prime number generator
        chars_map = dict( [ (x,primes.next()) for x,y in \
            sorted( counts.items(), key=lambda i:i[1],
                reverse=True ) ] )

        # Recast the dict as a list, where the index is the index
        # in the alphabet. The value is the prime number for that
        # character.

        self.chars_list = [ chars_map[chr(x)] for x in range(ord('a'), ord('z') + 1) ]

        addTiming( 'Assign Primes to the alphabet.' )


        # Insert all the dictionary words into the list
        self.sigs = collections.defaultdict( list )
        for word in all_lines:
            sig = self.__getSignature( word )
            if sig > 1:    # ignore lines without letters
                self.sigs[ sig ].append( word )


        # We need the keys in list form so we can have it sorted.
        # Lookups into the signatures dictionary are pretty rare.
        self.sigs_keys = sorted( self.sigs.keys() )
        addTiming( 'Create signatures dictionary.' )

    def __getSignatureKeys(self):
        '''Returns the sorted list of all signature keys. This is
        used to populate a list of all available words.'''
        return self.sigs_keys

    def formulateAnagramPhraseCombo(self, res):
        '''Render an anagram "phrase" into text for display. Each key
        is separate by double spaces, and each key displays as a comma
        separated list of the words choices.'''
        return "  ".join( [ ','.join(self.sigs[s]) for s in res ] )



    def __solveAnagramPhrase(self, letters, unreduced_keys, start=0, \
                so_far=[], display_progress=False):
        '''This is the recursive function that helps produce anagrams.
        It should not be called directly.'''

        # letters: Product of signatures of letters remaining.
        # unreduced_keys: Keys representing items in the dictionary
        #    that can non necessarily be reached by the remaining
        #    letters.
        # start: The index of unreduced_keys to start considering.
        #    keys before this do not need to be considered in
        #    combination with this pick because earlier keys
        #    will be considered separately and they will consider
        #    combining with this pick as part of their recursion.
        #    The start value should be considered again in case
        #    the same key can be used multiple times.
        # so_far: A list containing the keys that have been picked
        #    so far in this chain of recursions.
        # display_progress: Flag, if true then results are displayed
        #    as they are discovered.

        if letters == 1:
            # There are no letters left.
            if display_progress:
                print "Result: %s - %s" % \
                    ( repr(so_far),
                    self.formulateAnagramPhraseCombo(so_far) )
            return [ so_far ]

        # Filter list of keys to remove any that can no longer
        # be constructed using some of the input letters.
        reduced_keys = [ x for x in unreduced_keys[start:] if letters % x == 0 ]
        result = []

        # Recurse on all items remaining in the dictionary.
        for index,sig in enumerate(reduced_keys):
            remaining_letters = letters // sig
            result += self.__solveAnagramPhrase(
                    letters        = remaining_letters,
                    unreduced_keys    = reduced_keys,
                    start         = index,
                    so_far        = so_far + [ sig ],
                    display_progress= display_progress
                    )

        return result


    def anagrams( self, phrase_string, display_progress=False ):
        '''This function takes an input phrase string and returns
        a list of all anagrams that can be generated from it. The
        return value is a list of lists of lists. The inner lists
        represent the individual words which are interchangeable
        in an anagram. For instance, "tarp" and "trap" are
        anagrams of each other. Whenever one can be used, the
        other can substitute. They will be presented together
        in the innermost list. An example output for "lumberjack"
        might be:
        [ [ ['me'], ['bark'], ['Cluj'] ],
          [ ['me'], ['blur','burl'], ['jack'], ],
          [ ['be'], ['mark'], ['Cluj'] ]
          [ ['am'], ['jerk'], ['club'] ]
          [ ['elm','Mel'], ['jar'], ['buck'] ]
          ...
          ]
        '''
        all_keys = self.__getSignatureKeys()
        if options.dumpdict:
            for k,v in sorted(sigs.items(), key=lambda x: x[0]):
                print repr(k),'->',repr(v)

        r = self.__solveAnagramPhrase(
                self.__getSignature(phrase_string),
                all_keys,
                display_progress=display_progress )

        r = [ [ self.sigs[s] for s in row ] for row in r ]
        addTiming( 'Solve anagrams for "%s": %d rows' % (phrase_string, len(r),) )
        return r






if __name__ == "__main__":
    import optparse

    description = '''\
Anagram generator by Mark Santesson. This program rearranges letters
in any non-option command line parameters and output the anagrams
that can be generated from them. The potential words are filtered
through a dictionary. To generate anagrams for more than one phrase,
separate the phrases with (escaped) semicolons.
'''

    parser = optparse.OptionParser(
                usage='usage: %prog [options] args',
                description=description )
    parser.add_option('-t', '--time', action='store_true', default=False,
            dest='timing', help='Display timing information but not anagrams generated.')
    parser.add_option('-d', '--dictionary', default='words',
            dest='dictionary_name',
            help='Specify a location for the dictionary. Default is "%default".')
    parser.add_option('--dumpdict', action='store_true', default=False,
            dest='dumpdict',
            help='Dump dictionary after load, for debug purposes.')

    options, test = parser.parse_args()

    if len(test) >= 1:
        test = ' '.join(test).split(';')
    else:
        test = [ "face", "astronomy", "SETEC Astronomy" ]

    ag = AnagramGenerator( options.dictionary_name )
    for x in test:
        print "%s:" % x
        ag.anagrams( x, not options.timing )

    if options.timing:
        print "Timings:"
        for et,desc in timings:
            print "%f - %s" % (et, desc,)
    print "Done.\n"


# 932 seconds to solve SETEC Astronomy without limiting dictionary.
# The C version took 161 secs.
# 21 seconds after reducing the keys from the dict.
# With dictionary reduction at every recursion, it goes down to 4.25 seconds.

