# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import sys


class Buffer(object):
    """Abstract base class for all Buffer objects.

    You should treat Buffer objects as immutable.

    """
    def __init__(self, filename='<data>', position=0, line_number=1, column_number=1):
        """If `position` is given, `line_number` and `column_number` should
        be given too, to match.

        """
        self._filename = filename
        self.position = position
        self._line_number = line_number
        self._column_number = column_number

    @property
    def filename(self):
        return self._filename

    @property
    def line_number(self):
        return self._line_number

    @property
    def column_number(self):
        return self._column_number

    def advance(self, inp):
        """Given a string that we have just consumed from the buffer,
        return new line_number and column_number.

        """
        line_number = self.line_number
        column_number = self.column_number
        for char in inp:
            if char == '\n':
                line_number += 1
                column_number = 1
            else:
                column_number += 1
        return (line_number, column_number)

    def chop(self, amount):
        raise NotImplementedError

    def first(self, amount):
        raise NotImplementedError

    def is_at_eof(self):
        raise NotImplementedError

    def is_at_utf8(self):
        k = ord(self.first(1))
        if k & 0b11100000 == 0b11000000:
            return 2
        elif k & 0b11110000 == 0b11100000:
            return 3
        elif k & 0b11111000 == 0b11110000:
            return 4
        else:
            return 0

    def isalnum(self):
        return self.first(1).isalnum()

    def startswith(self, strings):
        for s in strings:
            if self.first(len(s)) == s:
                return True
        return False

    def copy(self):
        raise NotImplementedError


class StringBuffer(Buffer):
    def __init__(self, string, **kwargs):
        """Create a new StringBuffer object.

        `string` should be a raw string, not unicode.  If `position` is given,
        `line_number` and `column_number` should be given too, to match.

        """
        assert not isinstance(string, unicode)
        self.string = string
        Buffer.__init__(self, **kwargs)

    def __str__(self):
        return self.string

    def __repr__(self):
        return "StringBuffer(%r, filename=%r, position=%r, line_number=%r, column_number=%r)" % (
            self.string, self.filename, self.position, self.line_number, self.column_number
        )

    def chop(self, amount):
        assert self.position <= len(self.string) - amount, \
            "attempt made to chop past end of buffer"
        result = self.string[self.position:self.position + amount]

        (line_number, column_number) = self.advance(result)
        new_buffer = StringBuffer(self.string,
            filename=self._filename,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )

        return (result, new_buffer)

    def first(self, amount):
        if self.position > len(self.string) - amount:
            return None
        chars = self.string[self.position:self.position + amount]
        #print >>sys.stderr, "peeked '%s'" % chars
        return chars

    def is_at_eof(self):
        return self.position >= len(self.string)


class FileBuffer(Buffer):
    def __init__(self, file, **kwargs):
        self.file = file
        Buffer.__init__(self, **kwargs)
        try:
            j = self.file.read(1)
            self.init_pos = self.file.tell()
            self.file.seek(0, 0)
        except IOError as e:
            import sys
            print >>sys.stderr, "BAD"
            print "BAD"
            raise

    def chop(self, amount):
        self.file.seek(self.position, 0)
        result = self.file.read(amount)

        (line_number, column_number) = self.advance(result)
        new_buffer = FileBuffer(self.file,
            filename=self._filename,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )

        return (result, new_buffer)

    def first(self, amount):
        self.file.seek(self.position, 0)
        result = self.file.read(amount)
        self.file.seek(self.position, 0)

        return result

    def is_at_eof(self):
        return self.first(1) == ''
