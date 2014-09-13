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


class FileBuffer(Buffer):
    # Well, this was a nice try.  But the bottom line is that
    # filehandles are mutable :/ ... and Buffers can't be mutable
    # at all.  TODO: make it so that Buffers can be mutable, oi
    def __init__(self, file, pre_buffer='', **kwargs):
        self.file = file
        self.pre_buffer = pre_buffer
        Buffer.__init__(self, **kwargs)

    def get_bytes(self, amount):
        """Returns a new pre_buffer."""
        bytes_to_read = amount - len(self.pre_buffer)
        if bytes_to_read <= 0:
            return self.pre_buffer
        bytes = self.file.read(bytes_to_read)
        return self.pre_buffer + bytes

    def chop(self, amount):
        pre_buffer = self.get_bytes(amount)
        chars = pre_buffer[0:amount]
        remaining = pre_buffer[amount:]

        (line_number, column_number) = self.advance(chars)
        new_buffer = FileBuffer(self.file,
            filename=self._filename,
            pre_buffer=remaining,
            position=self.position + amount,
            line_number=line_number,
            column_number=column_number
        )
        self.file = None
        return (chars, new_buffer)

    def first(self, amount):
        pre_buffer = self.get_bytes(amount)
        chars = pre_buffer[0:amount]

        new_buffer = FileBuffer(self.file,
            filename=self._filename,
            pre_buffer=pre_buffer,
            position=self.position,
            line_number=self._line_number,
            column_number=self._column_number
        )
        self.file = None
        return (chars, new_buffer)
