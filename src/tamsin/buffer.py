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
    def __init__(self, file, **kwargs):
        self.file = file
        # stuff we have read out of the file, but need to keep
        self.pre_buffer = ''
        # the position in the file where we started reading into pre_buffer
        self.pre_position = 0
        self.stack = []
        Buffer.__init__(self, **kwargs)

    def save_state(self):
        state = (self.position, self.line_number, self.column_number)
        self.stack.append(state)

    def _truncate_pre_buffer(self):
        if not self.stack and self.position > self.pre_position:
            self.pre_buffer = self.pre_buffer[self.position - self.pre_position:]
            self.pre_position = self.position

    def restore_state(self):
        state = self.stack.pop()
        (self.position, self.line_number, self.column_number) = state
        self._truncate_pre_buffer()

    def pop_state(self):
        self.stack.pop()
        self._truncate_pre_buffer()

    def chop(self, amount):
        pos = self.position - self.pre_position
        bytes = self.pre_buffer[pos:pos + amount]
        bytes_to_read = amount - len(bytes)
        if bytes_to_read > 0:
            self.pre_buffer += self.file.read(bytes_to_read)
            bytes = self.pre_buffer[pos:pos + amount]
            #assert len(pre_bytes) == amount   # no, b/c what about EOF?

        self.position += amount
        (self.line_number, self.column_number) = self.advance(bytes)
        self._truncate_pre_buffer()
        return bytes

    def first(self, amount):
        self.save_state()
        bytes = self.chop(amount)
        self.restore_state()
        return bytes
