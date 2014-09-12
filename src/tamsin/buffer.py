# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import sys


class Buffer(object):
    def chop(self, amount):
        raise NotImplementedError

    def first(self, amount):
        raise NotImplementedError

    def is_at_eof(self):
        raise NotImplementedError

    def copy(self):
        raise NotImplementedError


class StringBuffer(Buffer):
    def __init__(self, string, filename='<data>', position=0, line_number=1, column_number=1):
        assert not isinstance(string, unicode)
        self.string = string
        self.position = position
        self._filename = filename
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

    def __str__(self):
        return self.string

    def __repr__(self):
        return "StringBuffer(%r, filename=%r, position=%r, line_number=%r, column_number=%r)" % (
            self.string, self.filename, self.position, self.line_number, self.column_number
        )

    def __eq__(self, other):
        return (self.string == other.string and
                self._filename == other.filename and
                self.position == other.position and
                self._line_number == other.line_number and
                self._column_number == other.column_number)

    def chop(self, amount):
        assert self.position <= len(self.string) - amount, \
            "attempt made to chop past end of buffer"
        result = self.string[self.position:self.position + amount]

        line_number = self.line_number
        column_number = self.column_number
        for char in result:
            if char == '\n':
                line_number += 1
                column_number = 1
            else:
                column_number += 1

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

    def copy(self):
        return StringBuffer(self.string, position=self.position)
