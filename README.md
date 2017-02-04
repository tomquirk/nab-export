# Smart transactions exporter for NAB

## Intro

This is a fork from ArtS repo `nab-export`. Whereas his performs export to QIF, I've stripped it out and am simply storing it to sqlite.
If you wish to get a CSV, simply generate it from the sqlite store.

## Prerequisites

- An account with NAB
- Internet banking login details - username and password
- Python 2.7
- Python libs mechanize and BeautifulSoup installed


## Usage

1. `python export.py`
2. Enter username and pass (or create `.credentials` file containing usernam and pass (separated by line))


## Privacy and Security

The tool does not use your username and password for anything except logging into NAB's website.

It does not store your username and password on the disk, you have to enter them every time you run it.

You can avoid that by creating a file named *.credentials* in the same folder. The file needs to have two lines, with username on the first line and password on the second line.


## Warranty

The Software is provided "as is" without warranty of any kind, either express or implied, including without limitation any implied warranties of condition, uninterrupted use, merchantability, fitness for a particular purpose, or non-infringement


## License

Copyright (C) 2012 Artem Skvira

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
