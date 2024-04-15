#!/usr/bin/env python3

#Copyright 2022 Mark Santesson
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


import sys


USE_COLORS = sys.stdin.isatty()

escape = '\x1b[0m'
STYLES = { 'normal':0, 'bold':1, 'italic':3, 'underlined':4, 'blink':5, 'inverted':7, }
COLORS = { 'black':0, 'red':1, 'green':2, 'orange':3, 'blue':4, 'grey':5, 'brown':6, 'white':7, }

def make_color(style=0, fg=5, bg=0):
    style = STYLES.get(style, style)
    fg    = COLORS.get(fg, fg)
    bg    = COLORS.get(bg, bg)
    return f'\x1b[{style};{30+fg};{40+bg}m'

def wrap(text, color_str):
    if USE_COLORS:
        return f'{color_str}{text}{escape}'
    else:
        return text

red   = lambda t: wrap(t, make_color(0, 1, 0))
green = lambda t: wrap(t, make_color(0, 2, 0))
white = lambda t: wrap(t, make_color(0, 7, 0))


if __name__ == "__main__":
    print('This module is a utility module to support colors on the command line.')
    sys.exit(1)

