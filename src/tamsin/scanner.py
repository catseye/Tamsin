# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.event import EventProducer
from tamsin.term import Term, EOF


class Scanner(EventProducer):
    def __init__(self, buffer, position=0, listeners=None):
        """Create a new Scanner object.
        
        buffer should be a raw string, not unicode.

        """
        self.listeners = listeners
        self.event('set_buffer', buffer)
        self.buffer = buffer
        assert buffer is not None
        assert not isinstance(buffer, unicode)
        self.position = position
        self.reset_position = position
        self.engines = []

    def __repr__(self):
        return "Scanner(%r, position=%r)" % (
            self.buffer, self.position
        )

    def get_state(self):
        """Returns an object which saves the current state of this
        Scanner.

        """
        assert self.position == self.reset_position, \
            "scanner in divergent state: pos=%s, reset=%s" % (
                self.position, self.reset_position)
        return (self.position, self.buffer)

    def install_state(self, (position, buffer)):
        """Restores the state of this Scanner to that which was saved by
        a previous call to get_state().

        """
        self.position = position
        self.reset_position = position
        self.buffer = buffer

    def push_engine(self, engine):
        self.engines.append(engine)

    def pop_engine(self):
        self.engines.pop()

    def is_at_eof(self):
        """Returns True iff there is no more input to scan.

        Should only be used by ScannerEngines.  Parsing code should check
        to see if peek() is EOF instead.

        """
        return self.position >= len(self.buffer)

    def is_at_utf8(self):
        """Returns the number of bytes following that comprise a UTF-8
        character.  Will be 0 for non-UTF-8 characters.

        Should only be used by ScannerEngines.

        """
        k = ord(self.buffer[self.position])
        if k & 0b11100000 == 0b11000000:
            return 2
        if k & 0b11110000 == 0b11100000:
            return 3
        if k & 0b11111000 == 0b11110000:
            return 4
        return 0
        
    def chop(self, amount):
        """Returns amount characters from the buffer and advances the
        scan position by amount.

        Should only be used by ScannerEngines.

        """
        if self.position > len(self.buffer) - amount:
            raise ValueError("internal: tried to chop past end of buffer")
        result = self.buffer[self.position:self.position+amount]
        self.event('chopped', result)
        self.position += amount
        return result

    def startswith(self, strings):
        for s in strings:
            if self.buffer[self.position:self.position+len(s)] == s:
                return True
        return False

    def isalnum(self):
        return self.buffer[self.position].isalnum()

    def report_buffer(self, position, length):
        """Display a printable snippet of the buffer, of maximum
        length length, starting at position.

        """
        report = self.buffer[position:position+length]
        if len(report) == length:
            report += '...'
        return repr(report)

    def error(self, expected):
        raise ValueError(u"Expected %s at %s (position %s)" %
                         (expected,
                          self.report_buffer(self.position, 20),
                          self.position))

    def scan(self):
        """Returns the next token from the buffer.
        
        You MUST call either commit() or unscan() after calling this,
        as otherwise the position and reset_position will be divergent
        (and you will trigger an assert when you try to scan().)
        If you want to just see what the next token would be, call peek().

        The returned token will always be a raw string, possibly
        containing UTF-8 sequences, possibly not.

        """
        assert self.position == self.reset_position, \
            "scanner in divergent state: pos=%s, reset=%s" % (
                self.position, self.reset_position)
        token = self.engines[-1].scan_impl(self)
        assert not isinstance(token, unicode), repr(token)
        self.event('scanned', self, token)
        return token

    def unscan(self):
        self.position = self.reset_position

    def commit(self):
        self.reset_position = self.position

    def peek(self):
        before = self.position
        token = self.scan()
        self.unscan()
        after = self.position
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
        print "--" * indent + "buffer: '%s'" % self.buffer
        print "--" * indent + "position: %s" % self.position
        print "--" * indent + "buffer at position: '%s'" % self.report_buffer(self.position, 40)
        print "--" * indent + "reset_position: %s" % self.reset_position
        print "--" * indent + "buffer at reset_pos: '%s'" % self.report_buffer(self.reset_position, 40)


class ScannerEngine(object):
    def scan_impl(self, scanner):
        """Should always return a Unicode string."""
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
            else:
                scanner.error('identifiable character')

        if scanner.startswith(('=', '(', ')', '[', ']', '{', '}', '!', ':', '/',
                            '|', '&', ',', '.', '@', '+', '$',
                            )):
            return scanner.chop(1)

        for quote in (CLOSE_QUOTE.keys()):
            if scanner.startswith((quote,)):
                token = quote
                scanner.chop(1)
                while (not scanner.is_at_eof() and
                       not scanner.startswith((CLOSE_QUOTE[quote],))):
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
                scanner.chop(1)  # chop ending quote
                # we add the specific close quote we expect, in case it was EOF
                token += CLOSE_QUOTE[quote]
                return token

        if scanner.isalnum():
            token = ''
            while not scanner.is_at_eof() and (scanner.isalnum() or
                                               scanner.startswith(('_',))):
                token += scanner.chop(1)
            return token

        scanner.error('identifiable character')


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
        #assert self.interpreter.scanner = my scanner
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
        save_reset_position = scanner.reset_position
        result = self.interpreter.interpret(self.production)
        (success, token) = result
        scanner.reset_position = save_reset_position

        if success:
            self.interpreter.event('production_scan', self.production, token)
            assert isinstance(token, Term)
            if token is EOF:
                return token
            return str(token)
        else:
            return EOF
