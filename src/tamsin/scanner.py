# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.event import EventProducer
from tamsin.term import Term


EOF = object()


class ScannerState(object):
    def __init__(self, buffer, position=0, line_number=1, column_number=1):
        """Create a new ScannerState object.

        You should treat these as immutable.

        buffer should be a raw string, not unicode.  If position is given,
        line_number and column_number should be given too, to match.

        """
        assert buffer is not None
        assert not isinstance(buffer, unicode)
        self._buffer = buffer
        self._position = position
        self._line_number = line_number
        self._column_number = column_number

    @property
    def buffer(self):
        return self._buffer

    @property
    def position(self):
        return self._position

    @property
    def line_number(self):
        return self._line_number

    @property
    def column_number(self):
        return self._column_number

    def is_at_eof(self):
        return self.position >= len(self.buffer)

    def is_at_utf8(self):
        k = ord(self.buffer[self.position])
        if k & 0b11100000 == 0b11000000:
            return 2
        elif k & 0b11110000 == 0b11100000:
            return 3
        elif k & 0b11111000 == 0b11110000:
            return 4
        else:
            return 0

    def isalnum(self):
        return self.buffer[self.position].isalnum()

    def chop(self, amount):
        if self.position > len(self.buffer) - amount:
            raise ValueError("internal: tried to chop past end of buffer")
        result = self.buffer[self.position:self.position + amount]
        line_number = self.line_number
        column_number = self.column_number
        for char in result:
            if char == '\n':
                line_number += 1
                column_number = 1
            else:
                column_number += 1
        
        return (result, ScannerState(self.buffer, position=self.position + amount,
                                     line_number=line_number, column_number=column_number))

    def startswith(self, strings):
        for s in strings:
            if self.buffer[self.position:self.position+len(s)] == s:
                return True
        return False

    def report_buffer(self, position, length):
        report = self.buffer[position:position+length]
        if len(report) == length:
            report += '...'
        return repr(report)

    def __eq__(self, other):
        return (self.buffer == other.buffer and
                self.position == other.position and
                self.line_number == other.line_number and
                self.column_number == other.column_number)

    def __repr__(self):
        return "ScannerState(%r, position=%r, line_number=%r, column_number=%r)" % (
            self.buffer, self.position, self.line_number, self.column_number
        )


class Scanner(EventProducer):
    def __init__(self, state, listeners=None):
        """Create a new Scanner object.

        """
        self.listeners = listeners
        self.event('set_buffer', buffer)
        if not isinstance(state, ScannerState):
            state = ScannerState(str(state))
        self.state = state
        self.reset_state = state
        self.engines = []

    def __repr__(self):
        return "Scanner(%r, position=%r)" % (
            self.buffer, self.position
        )

    def get_state(self):
        """Returns an object which saves the current state of this
        Scanner.

        """
        assert self.state == self.reset_state, \
            "scanner in divergent state: %r vs %r" % (self.state, self.reset_state)
        return self.state

    def install_state(self, state):
        """Restores the state of this Scanner to that which was saved by
        a previous call to get_state().

        """
        self.state = state
        # ... TODO ... wat ... do we really need reset_state anyway?
        self.reset_state = state

    def push_engine(self, engine):
        #print repr(('push', engine))
        self.engines.append(engine)

    def pop_engine(self):
        engine = self.engines.pop()
        #print repr(('pop', engine))

    def is_at_eof(self):
        """Returns True iff there is no more input to scan.

        Should only be used by ScannerEngines.  Parsing code should check
        to see if ... something

        """
        return self.state.is_at_eof()

    def is_at_utf8(self):
        """Returns the number of bytes following that comprise a UTF-8
        character.  Will be 0 for non-UTF-8 characters.

        Should only be used by ScannerEngines.

        """
        return self.state.is_at_utf8()

    def chop(self, amount):
        """Returns amount characters from the buffer and advances the
        scan position by amount.

        Should only be used by ScannerEngines.

        """
        (result, state) = self.state.chop(amount)
        self.state = state
        return result

    def startswith(self, strings):
        return self.state.startswith(strings)

    def isalnum(self):
        return self.state.isalnum()

    def report_buffer(self, position, length):
        """Display a printable snippet of the buffer, of maximum
        length length, starting at position.

        """
        return self.state.report_buffer(position, length)

    def error(self, expected):
        raise ValueError(u"expected %s at line %s, column %s in `filename`" %
                         (expected,
                          self.state.line_number,
                          self.state.column_number))

    def scan(self):
        """Returns the next token from the buffer.
        
        You MUST call either commit() or unscan() after calling this,
        as otherwise the position and reset_position will be divergent
        (and you will trigger an assert when you try to scan() next.)
        If you want to just see what the next token would be, call peek().

        The returned token will always be a raw string, possibly
        containing UTF-8 sequences, possibly not.

        """
        assert self.state == self.reset_state, \
            "scanner in divergent state: %r vs %r" % (self.state, self.reset_state)
        token = self.engines[-1].scan_impl(self)
        assert not isinstance(token, unicode), repr(token)
        self.event('scanned', self, token)
        return token

    def unscan(self):
        self.state = self.reset_state

    def commit(self):
        self.reset_state = self.state

    def peek(self):
        before = self.state
        token = self.scan()
        self.unscan()
        after = self.state
        assert before == after, "unscan did not restore position"
        return token

    def consume(self, t):
        if isinstance(t, unicode):
            t = t.encode('UTF-8')
        assert not isinstance(t, unicode)
        self.event('consume', t)
        if self.scan() == t:
            self.commit()
            return t
        else:
            self.unscan()
            return None

    def consume_any(self):
        tok = self.scan()
        self.commit()
        return tok
    
    def expect(self, t):
        r = self.consume(t)
        if r is None:
            self.error("'%s'" % t)
        return r
    
    def dump(self, indent=1):
        print "==" * indent + "%r" % self
        print "--" * indent + "engines: %r" % repr(self.engines)
        print "--" * indent + "state: %r" % self.state
        print "--" * indent + "reset_state: %r" % self.reset_state


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
                scanner.error('identifiable character')

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

        scanner.error('identifiable character')

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
                    scanner.error('legal escape sequence')
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
        #print repr(scanner.buffer[scanner.position])
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
        # if we ever go back to exceptions, we would have a try/catch here
        
        # this will cause the scanner to have another engine pushed onto
        # it.  we rely on that engine to actually get us the token, and it
        # will update the scanner for us.
        #
        # BUT the subsidiary scanner may have commited, while WE want to
        # leave the scanner in a divergent state.  So we save the reset
        # position, and restore it when the subsidiary scan is done.

        assert scanner is self.interpreter.scanner

        # default to this so you don't shoot yourself in the foot
        scanner.push_engine(UTF8ScannerEngine())

        save_state = scanner.reset_state
        result = self.interpreter.interpret(self.production)
        (success, token) = result
        scanner.reset_state = save_state

        scanner.pop_engine()

        if success:
            self.interpreter.event('production_scan', self.production, token)
            assert isinstance(token, Term), repr(token)
            if token is EOF:
                return token
            return str(token)
        else:
            return EOF
