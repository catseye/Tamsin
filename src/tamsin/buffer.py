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
        """Returns a pair of `amount` characters chopped off the front of
        the buffer, and a new Buffer object.

        """
        raise NotImplementedError

    def first(self, amount):
        """Returns a pair of the first `amount` characters in the buffer
        (without consuming them) and a new Buffer object.

        """
        raise NotImplementedError

    def is_at_eof(self):
        """Returns a pair of a boolean and a new Buffer object.

        """
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
        chars = self.string[self.position:self.position + amount]

        (line_number, column_number) = self.advance(chars)
        new_buffer = StringBuffer(self.string,
            filename=self._filename,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )

        return (chars, new_buffer)

    def first(self, amount):
        #assert self.position <= len(self.string) - amount, \
        #    "attempt made to first past end of buffer"
        #if self.position > len(self.string) - amount:
        #    return None
        chars = self.string[self.position:self.position + amount]

        # did not modify self, so it's OK to return it
        return (chars, self)

    def is_at_eof(self):
        at_eof = self.position >= len(self.string)

        # did not modify self, so it's OK to return it
        return (at_eof, self)


class FileBuffer(Buffer):
    def __init__(self, file, **kwargs):
        self.file = file
        assert False, "do not use!"
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

        new_buffer = FileBuffer(self.file,
            filename=self._filename,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )
        return (result, new_buffer)

    def is_at_eof(self):
        at_eof = self.first(1) == ''

        new_buffer = FileBuffer(self.file,
            filename=self._filename,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )
        return (at_eof, new_buffer)
