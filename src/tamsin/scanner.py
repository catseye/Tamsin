# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.buffer import Buffer
from tamsin.event import EventProducer
from tamsin.term import Term


EOF = object()


class Scanner(EventProducer):
    def __init__(self, buffer, engines=None, listeners=None):
        """Create a new Scanner object.

        """
        self.listeners = listeners
        self.event('set_buffer', buffer)
        assert isinstance(buffer, Buffer)
        self.buffer = buffer
        self.engines = []
        if engines is not None:
            for engine in engines:
                self.push_engine(engine)

    def __repr__(self):
        return "Scanner(%r, position=%r)" % (
            self.buffer, self.position
        )

    def get_state(self):
        """Returns an object which saves the current state of this
        Scanner.

        """
        return self.buffer

    def install_state(self, state):
        """Restores the state of this Scanner to that which was saved by
        a previous call to get_state().

        """
        self.buffer = state

    def push_engine(self, engine):
        self.engines.append(engine)

    def pop_engine(self):
        engine = self.engines.pop()

    # # # # # # # Buffer interface # # # # # # #
    #
    #  These methods hide the immutability of Buffer.
    #

    def chop(self, amount):
        """Returns amount characters from the buffer and advances the
        scan position by amount.

        Should only be used by ScannerEngines.

        """
        (chars, buffer) = self.buffer.chop(amount)
        self.buffer = buffer
        return chars

    def first(self, amount):
        """Returns amount characters from the buffer.  Does not advance the
        scan position.

        Should only be used by ScannerEngines, and then only in error
        reporting.

        """
        (chars, buffer) = self.buffer.first(amount)
        self.buffer = buffer
        return chars

    # # # # # # # # # # # # # # # # # # # # # #

    def is_at_eof(self):
        """Returns True iff there is no more input to scan.

        Should only be used by ScannerEngines.  Parsing code should check
        to see if ... something

        """
        return self.first(1) == ''

    def is_at_utf8(self):
        """Returns the number of bytes following that comprise a UTF-8
        character.  Will be 0 for non-UTF-8 characters.

        Should only be used by ScannerEngines.

        """
        k = ord(self.first(1))
        if k & 0b11100000 == 0b11000000:
            return 2
        elif k & 0b11110000 == 0b11100000:
            return 3
        elif k & 0b11111000 == 0b11110000:
            return 4
        else:
            return 0

    def startswith(self, strings):
        for s in strings:
            if self.first(len(s)) == s:
                return True
        return False

    def isalnum(self):
        return self.first(1).isalnum()

    def error_message(self, expected, found):
        if found is EOF:
            found = 'EOF'
        else:
            found = "'%s'" % found
        return (
            "expected %s but found %s at line %s, column %s in '%s'" %
            (expected, found,
             self.buffer.line_number,
             self.buffer.column_number,
             self.buffer.filename)
        )

    def error(self, expected, found):
        raise ValueError(self.error_message(expected, found))

    def scan(self):
        """Returns the next token from the buffer.

        This method consumes the token.  If you want to just see
        what the next token would be, call peek() instead.

        The returned token will always be a raw string, possibly
        containing UTF-8 sequences, possibly not.

        """
        token = self.engines[-1].scan_impl(self)
        #import sys
        #print >>sys.stderr, token
        assert not isinstance(token, unicode), repr(token)
        self.event('scanned', self, token)
        return token

    def peek(self):
        backup = self.get_state()
        token = self.scan()
        self.install_state(backup)
        return token

    def consume(self, t):
        if isinstance(t, unicode):
            t = t.encode('UTF-8')
        assert not isinstance(t, unicode)
        self.event('consume', t)
        backup = self.get_state()
        s = self.scan()
        if s == t:
            return t
        else:
            self.install_state(backup)
            return None

    def expect(self, t):
        r = self.consume(t)
        if r is None:
            self.error("'%s'" % t, self.scan())
        return r
    
    def dump(self, indent=1):
        print "==" * indent + "%r" % self
        print "--" * indent + "engines: %r" % repr(self.engines)
        print "--" * indent + "buffer: %r" % self.buffer


class ScannerEngine(object):
    def scan_impl(self, scanner):
        """Should always return a non-Unicode string."""
        raise NotImplementedError


CLOSE_QUOTE = {
    '"': '"',
    '\'': '\'',
}

ESCAPE_SEQUENCE = {
    'r': "\r",
    'n': "\n",
    't': "\t",
    "'": "'",
    '"': '"',
    '\\': '\\',
}


class TamsinScannerEngine(ScannerEngine):
    def scan_impl(self, scanner):
        while not scanner.is_at_eof() and scanner.startswith(('#', ' ', '\t', '\r', '\n')):
            while not scanner.is_at_eof() and scanner.startswith((' ', '\t', '\r', '\n')):
                scanner.chop(1)
            while not scanner.is_at_eof() and scanner.startswith(('#',)):
                while not scanner.is_at_eof() and not scanner.startswith(('\n',)):
                    scanner.chop(1)
                if not scanner.is_at_eof():
                    scanner.chop(1)

        if scanner.is_at_eof():
            return EOF

        if scanner.startswith(('&&', '||', '->', '<-', '<<', '>>')):
            return scanner.chop(2)

        c = scanner.is_at_utf8()
        if c > 0:
            c = scanner.chop(c).decode('UTF-8')
            if c in (u'→', u'←', u'«', u'»'):
                return c.encode('UTF-8')
            elif c == u'“':
                return self.consume_quoted(scanner,
                    u'“'.encode('UTF-8'), u'”'.encode('UTF-8')
                )
            else:
                scanner.error('identifiable character', scanner.first(1))

        if scanner.startswith(('=', '(', ')', '[', ']', '{', '}', '!', ':', '/',
                            '|', '&', ',', '.', '@', '+', '$',
                            )):
            return scanner.chop(1)

        for quote in (CLOSE_QUOTE.keys()):
            if scanner.startswith(quote):
                scanner.chop(len(quote))
                return self.consume_quoted(scanner, quote, CLOSE_QUOTE[quote])

        if scanner.isalnum():
            token = ''
            while not scanner.is_at_eof() and (scanner.isalnum() or
                                               scanner.startswith(('_',))):
                token += scanner.chop(1)
            return token

        scanner.error('identifiable character', scanner.first(1))

    def consume_quoted(self, scanner, quote, close_quote):
        # assumes the start quote has already been chopped
        token = quote
        while (not scanner.is_at_eof() and
               not scanner.startswith(close_quote)):
            char = scanner.chop(1)
            if char == '\\':
                char = scanner.chop(1)
                if char in ESCAPE_SEQUENCE:
                    char = ESCAPE_SEQUENCE[char]
                elif char == 'x':
                    char = chr(int(scanner.chop(2), 16))
                else:
                    scanner.error('legal escape sequence', '\\' + char)
            token += char
        scanner.chop(len(close_quote))  # chop ending quote
        # we add the specific close quote we expect, in case it was EOF
        token += close_quote
        return token


class UTF8ScannerEngine(ScannerEngine):
    def scan_impl(self, scanner):
        if scanner.is_at_eof():
            return EOF
        c = scanner.is_at_utf8()
        if c > 0:
            return scanner.chop(c)
        return scanner.chop(1)


class ByteScannerEngine(ScannerEngine):
    def scan_impl(self, scanner):
        if scanner.is_at_eof():
            return EOF
        return scanner.chop(1)


class ProductionScannerEngine(ScannerEngine):
    """A ScannerEngine that uses a production of the Tamsin program to
    scan the input.

    """
    def __init__(self, interpreter, production):
        self.interpreter = interpreter
        self.production = production

    def scan_impl(self, scanner):
        if scanner.is_at_eof():
            return EOF

        # This will cause the scanner to have another engine pushed onto
        # it.  We rely on that engine to actually get us the token, and it
        # will update the scanner for us.

        assert scanner is self.interpreter.scanner

        # default to this so you don't shoot yourself in the foot
        scanner.push_engine(UTF8ScannerEngine())

        result = self.interpreter.interpret(self.production)
        (success, token) = result

        scanner.pop_engine()

        if success:
            self.interpreter.event('production_scan', self.production, token)
            assert isinstance(token, Term), repr(token)
            if token is EOF:
                return token
            return str(token)
        else:
            return EOF
