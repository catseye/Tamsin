# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import sys


class Buffer(object):
    """Abstract base class for all Buffer objects.

    Buffer objects are mutable, but must be capable of saving and restoring
    their state indefinitely.

    """
    def __init__(self, filename='<data>', position=0, line_number=1, column_number=1):
        """If `position` is given, `line_number` and `column_number` should
        be given too, to match.

        """
        self.filename = filename
        self.position = position
        self.line_number = line_number
        self.column_number = column_number

    def save_state(self):
        raise NotImplementedError

    def restore_state(self):
        raise NotImplementedError

    def pop_state(self):
        raise NotImplementedError

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
        self.stack = []
        Buffer.__init__(self, **kwargs)

    def save_state(self):
        self.stack.append((self.position, self.line_number, self.column_number))

    def restore_state(self):
        (self.position, self.line_number, self.column_number) = self.stack.pop()

    def pop_state(self):
        self.stack.pop()

    def __str__(self):
        return self.string

    def __repr__(self):
        return "StringBuffer(%r, filename=%r, position=%r, line_number=%r, column_number=%r)" % (
            self.string, self.filename, self.position, self.line_number, self.column_number
        )

    def chop(self, amount):
        assert self.position <= len(self.string) - amount, \
            "attempt made to chop past end of buffer"
        bytes = self.string[self.position:self.position + amount]

        self.position += amount
        (self.line_number, self.column_number) = self.advance(bytes)

        return bytes

    def first(self, amount):
        bytes = self.string[self.position:self.position + amount]

        return bytes


class FileBuffer(Buffer):
    # Well, this was a nice try.  But the bottom line is that
    # filehandles are mutable :/ ... and Buffers can't be mutable
    # at all.  TODO: make it so that Buffers can be mutable, oi
    def __init__(self, file, pre_buffer='', **kwargs):
        assert False, 'NO'
        self.file = file
        self.pre_buffer = pre_buffer
        self.stack = []
        Buffer.__init__(self, **kwargs)

    def save_state(self):
        self.stack.append((self.position, self.line_number, self.column_number))

    def restore_state(self):
        (self.position, self.line_number, self.column_number) = self.stack.pop()

    def pop_state(self):
        self.stack.pop()

    def get_bytes(self, amount):
        """Returns a new pre_buffer."""
        bytes_to_read = amount - len(self.pre_buffer)
        if bytes_to_read <= 0:
            return self.pre_buffer
        bytes = self.file.read(bytes_to_read)
        return self.pre_buffer + bytes

    def chop(self, amount):
        pre_buffer = self.get_bytes(amount)
        bytes = pre_buffer[0:amount]
        remaining = pre_buffer[amount:]

        (self.line_number, self.column_number) = self.advance(bytes)
        return bytes

    def first(self, amount):
        pre_buffer = self.get_bytes(amount)
        bytes = pre_buffer[0:amount]

        return bytes
