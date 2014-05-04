# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.event import EventProducer


class EOF(object):
    def __str__(self):
        return "EOF"
    def __repr__(self):
        return "EOF"
EOF = EOF()  # unique


def enc(x):
    if isinstance(x, str):
        x = x.decode('UTF-8')
        assert isinstance(x, unicode)
    else:
        x = unicode(x)
    return x.encode('ascii', 'xmlcharrefreplace')


class Scanner(EventProducer):
    def __init__(self, buffer, position=0, listeners=None):
        """Does NOT call scan() for you.  You should do that only when
        you want to scan a token (not before.)

        """
        self.listeners = listeners
        self.event('set_buffer', buffer)
        self.buffer = buffer
        assert buffer is not None
        self.position = position
        self.reset_position = position
        self.engines = []

    def __repr__(self):
        return "Scanner(%r, position=%r)" % (
            self.buffer, self.position
        )

    def get_state(self):
        assert self.position == self.reset_position, \
            "scanner in divergent state: pos=%s, reset=%s" % (
                self.position, self.reset_position)
        return (self.position, self.buffer)

    def install_state(self, (position, buffer)):
        self.position = position
        self.reset_position = position
        self.buffer = buffer

    def push_engine(self, engine):
        self.engines.append(engine)

    def pop_engine(self):
        self.engines.pop()
    
    def eof(self):
        return self.position >= len(self.buffer)

    def chop(self, amount):
        if self.eof():
            return None
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
        return enc(report)

    def error(self, expected):
        raise ValueError(u"Expected %s at '%s' (position %s)" %
                         (enc(expected),
                          self.report_buffer(self.position, 20),
                          self.position))

    def scan(self):
        """Returns the next token from the buffer.
        
        You MUST call either commit() or unscan() after calling this,
        as otherwise the position and reset_position will be divergent
        (and you will trigger an assert when you try to scan().)
        If you want to just see what the next token would be, call peek().

        """
        assert self.position == self.reset_position, \
            "scanner in divergent state: pos=%s, reset=%s" % (
                self.position, self.reset_position)
        tok = self.engines[-1].scan_impl(self)
        self.event('scanned', self, tok)
        return tok

    def unscan(self):
        self.position = self.reset_position

    def commit(self):
        self.reset_position = self.position

    def peek(self):
        before = self.position
        tok = self.scan()
        self.unscan()
        after = self.position
        assert before == after, "unscan did not restore position"
        return tok

    def consume(self, t):
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
        print "--" * indent + "buffer: '%s'" % enc(self.buffer)
        print "--" * indent + "position: %s" % self.position
        print "--" * indent + "buffer at position: '%s'" % self.report_buffer(self.position, 40)
        print "--" * indent + "reset_position: %s" % self.reset_position
        print "--" * indent + "buffer at reset_pos: '%s'" % self.report_buffer(self.reset_position, 40)


class ScannerEngine(object):
    pass


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
        while not scanner.eof() and scanner.startswith(('#', ' ', '\t', '\r', '\n')):
            while not scanner.eof() and scanner.startswith((' ', '\t', '\r', '\n')):
                scanner.chop(1)
            while not scanner.eof() and scanner.startswith(('#',)):
                while not scanner.eof() and not scanner.startswith(('\n',)):
                    scanner.chop(1)
                scanner.chop(1)

        if scanner.eof():
            return EOF

        if scanner.startswith(('&&', '||', '->', '<-', '<<', '>>')):
            return scanner.chop(2)

        if scanner.startswith(('=', '(', ')', '[', ']', '{', '}', '!',
                            '|', '&', u'→', u'←', ',', '.', '@', '+', '$',
                            u'«', u'»')):
            return scanner.chop(1)

        for quote in (CLOSE_QUOTE.keys()):
            if scanner.startswith((quote,)):
                tok = quote
                scanner.chop(1)
                while (not scanner.eof() and
                       not scanner.startswith((CLOSE_QUOTE[quote],))):
                    char = scanner.chop(1)
                    if char == '\\':
                        char = scanner.chop(1)
                        if char in ESCAPE_SEQUENCE:
                            char = ESCAPE_SEQUENCE[char]
                        else:
                            scanner.error('legal escape sequence')
                    tok += char
                scanner.chop(1)  # chop ending quote
                tok += CLOSE_QUOTE[quote]  # we add specific, in cas it was EOF
                return tok

        if scanner.isalnum():
            tok = ''
            while not scanner.eof() and (scanner.isalnum() or
                                         scanner.startswith(('_',))):
                tok += scanner.chop(1)
            return tok

        scanner.error('identifiable character')


class CharScannerEngine(ScannerEngine):
    def scan_impl(self, scanner):
        if scanner.eof():
            return EOF
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
        if scanner.eof():
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
        (success, tok) = result
        scanner.reset_position = save_reset_position

        if success:
            self.interpreter.event('production_scan', self.production, tok)
            if tok is EOF:
                return tok
            return unicode(tok)
        else:
            return EOF
