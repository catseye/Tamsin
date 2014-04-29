#!/usr/bin/env python
# encoding: UTF-8

import codecs
import sys


class EOF(object):
    def __str__(self):
        return "EOF"
    def __repr__(self):
        return "EOF"
EOF = EOF()  # unique


def enc(x):
    if not isinstance(x, str):
        x = unicode(x)
    return x.encode('ascii', 'xmlcharrefreplace')


class Term(object):
    def __init__(self, name, contents=None):
        self.name = name
        if contents is None:
            contents = []
        self.contents = contents

    def expand(self, context):
        """Expands this term, returning a new term where, for all x, all
        occurrences of (VAR x) are replaced with the value of x in the
        given context.

        """
        return Term(self.name, [x.expand(context) for x in self.contents])

    def __str__(self):
        if not self.contents:
            return self.name
        return "%s(%s)" % (
            self.name, ', '.join([str(x) for x in self.contents])
        )

    def __repr__(self):
        # sigh
        return str(self)


class Variable(Term):
    def __init__(self, name):
        assert name[0].isupper()
        self.name = name
        self.contents = []

    def expand(self, context):
        return context.fetch(self.name)


class Concat(Term):
    def __init__(self, lhs, rhs):
        assert isinstance(lhs, Term)
        assert isinstance(rhs, Term)
        self.lhs = lhs
        self.rhs = rhs

    def expand(self, context):
        lhs = self.lhs.expand(context)
        rhs = self.rhs.expand(context)
        return Term(str(lhs) + str(rhs))

    def __str__(self):
        return "%s + %s" % (self.lhs, self.rhs)


class EventProducer(object):
    def event(self, tag, *data):
        if self.listeners is None:
            self.listeners = []
        for listener in self.listeners:
            listener.announce(tag, *data)

    def subscribe(self, listener):
        if self.listeners is None:
            self.listeners = []
        self.listeners.append(listener)


class DebugEventListener(object):
    def __init__(self):
        self.indent = 0

    def listen_to(self, producer):
        producer.subscribe(self)

    def putstr(self, s):
        print (self.indent * '  ' + s)

    def announce(self, tag, *data):
        if tag == 'enter_interpreter':
            self.indent += 1
        if tag == 'leave_interpreter':
            self.indent -= 1

        if tag in ('leave_interpreter', 'update_scanner'):
            new_scanner = data[0]
            old_scanner = data[1]
            if (isinstance(new_scanner, CharScanner) and
                isinstance(old_scanner, ProductionScanner)):
                self.putstr("%s %r" % (tag, data))
                new_scanner.dump(self.indent)
                old_scanner.dump(self.indent)
                self.putstr("")
        else:
            return

        # EVERYTHING
        self.putstr("%s %r" % (tag, data))
        for d in data:
            if getattr(d, 'dump', None) is not None:
                d.dump(self.indent)
        return
         
        if tag in ('enter_interpreter', 'leave_interpreter', 'succeed_or', 'fail_or', 'begin_or'):
            self.putstr("%s %r" % (tag, data))
            return
        elif tag in ('try_literal', 'consume_literal', 'fail_literal'):
            self.putstr("%s %r" % (tag, data))
            data[1].dump(self.indent)
            return
        else:
            return
        ###
        if tag in ('chopped', 'consume', 'scanned'): # ('interpret_ast', 'try_literal'):
            return
        elif tag in ('switched_scanner_forward', 'switched_scanner_back'):
            self.putstr(tag)
            data[0].dump()
            data[1].dump()
        else:
            self.putstr("%s %r" % (tag, data))


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
        raise ValueError(u"Expected %s' at '%s' (position %s)" %
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
    u'「': u'」',
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
        while scanner.startswith((' ', '\t', '\r', '\n')):
            scanner.chop(1)

        if scanner.eof():
            return EOF

        if scanner.startswith(('&&', '||')):
            tok = scanner.chop(1)
            scanner.chop(1)
            return tok
        
        if scanner.startswith(('=', '(', ')', '[', ']', '{', '}',
                            '|', '&', u'→', ',', '.', '@', '+',
                            u'•', u'□', u'☆', u'«', u'»')):
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
                return tok

        if not scanner.eof() and scanner.isalnum():
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
        subs_reset = scanner.reset_position
        scanner.reset_position = save_reset_position

        if success:
            #self.event('production_scan', self.production, tok)
            return str(tok)
        else:
            return EOF
            #raise ValueError("ProductionScanner FAILED.  Production used "
            #                 "by ProductionScanner MUST NOT FAIL, or "
            #                 "THIS HAPPENS.")


class Parser(EventProducer):
    def __init__(self, buffer, listeners=None):
        self.listeners = listeners
        self.scanner = Scanner(buffer, listeners=self.listeners)
        self.scanner.push_engine(TamsinScannerEngine())

    def eof(self):
        return self.scanner.eof()
    def chop(self, amount):
        return self.scanner.chop(amount)
    def startswith(self, strings):
        return self.scanner.startswith(strings)
    def isalnum(self):
        return self.scanner.isalnum()
    def error(self, expected):
        return self.scanner.error(expected)
    def peek(self):
        return self.scanner.peek()
    def consume(self, t):
        return self.scanner.consume(t)
    def consume_any(self):
        return self.scanner.consume_any()
    def expect(self, t):
        return self.scanner.expect(t)

    def grammar(self):
        prods = [self.production()]
        while self.peek() is not EOF:
            prods.append(self.production())
        return ('PROGRAM', prods)

    def production(self):
        name = self.consume_any()
        args = []
        if self.consume('('):
            if self.peek() != ')':
                args.append(self.term())
                while self.consume(','):
                    args.append(self.term())
            self.expect(')')
        elif self.consume('['):
            args = self.expr0()
            self.expect(']')
        self.expect('=')
        e = self.expr0()
        self.expect('.')
        return ('PROD', name, args, e)

    def expr0(self):
        lhs = self.expr1()
        while self.consume('|'):
            rhs = self.expr1()
            lhs = ('OR', lhs, rhs)
        return lhs

    def expr1(self):
        lhs = self.expr2()
        while self.consume('&'):
            rhs = self.expr2()
            lhs = ('AND', lhs, rhs)
        return lhs

    def expr2(self):
        lhs = self.expr3()
        if self.consume('using'):
            if self.consume(u'☆'):
                # TODO: 'tamsin' or 'char' is all
                scanner_name = self.consume_any()
            else:
                # TODO: a production name only
                scanner_name = self.consume_any()
            lhs = ('USING', lhs, scanner_name)
        return lhs

    def expr3(self):
        lhs = self.expr4()
        if self.consume(u'→'):
            v = self.variable()
            lhs = ('SEND', lhs, v)
        return lhs

    def expr4(self):
        if self.consume('('):
            e = self.expr0()
            self.expect(')')
            return e
        elif self.consume('['):
            e = self.expr0()
            self.expect(']')
            return ('OR', e, ('RETURN', Term('nil')))
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return ('WHILE', e)
        elif (self.peek() is not None and
              self.peek()[0] == '"'):
            literal = self.consume_any()[1:]
            return ('LITERAL', literal)
        elif self.consume(u'«'):
            t = self.term()
            self.expect(u'»')
            return ('EXPECT', t)
        elif self.consume('set'):
            v = self.variable()
            self.expect("=")
            t = self.term()
            return ('SET', v, t)
        elif self.consume('return'):
            t = self.term()
            return ('RETURN', t)
        elif self.consume('fail'):
            t = self.term()
            return ('FAIL', t)
        elif self.consume(u'□'):
            return ('EOF',)
        elif self.consume('print'):
            t = self.term()
            return ('PRINT', t)
        elif self.consume('any'):
            return ('ANY',)
        else:
            name = self.consume_any()
            args = []
            if self.consume('('):
                if self.peek() != ')':
                    args.append(self.term())
                    while self.consume(','):
                        args.append(self.term())
                self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.term()
            return ('CALL', name, args, ibuf)

    def variable(self):
        if self.peek()[0].isupper():
            var = self.consume_any()
            return Variable(var)
        else:
            self.error('variable')

    def term(self):
        lhs = self.term1()
        while self.consume(u'•') or self.consume('+'):
            rhs = self.term1()
            lhs = Concat(lhs, rhs)
        return lhs

    def term1(self):
        if self.peek()[0].isupper():
            return self.variable()
        elif (self.peek()[0].isalnum() or
              self.peek()[0][0] in (u'「', '\'')):
            atom = self.consume_any()
            if atom[0] in (u'「', '\''):
                atom = atom[1:]
            subs = []
            if self.consume('('):
                if self.peek() != ')':
                    subs.append(self.term())
                while self.consume(','):
                    subs.append(self.term())
                self.expect(')')
            return Term(atom, subs)
        else:
            self.error('term')


class Context(EventProducer):
    def __init__(self, listeners=None):
        self.listeners = listeners
        self.scopes = []

    def __repr__(self):
        return "Context(%r)" % (
            self.scopes
        )

    def push_scope(self, purpose):
        self.scopes.append({})
        self.event('push_scope', self)

    def pop_scope(self, purpose):
        self.scopes.pop()
        self.event('pop_scope', self)

    def clone(self):
        n = Context(listeners=self.listeners)
        for scope in self.scopes:
            n.scopes.append(scope.copy())
        return n

    def fetch(self, name):
        self.event('fetch', name,
            self.scopes[-1].get(name, 'undefined'), self.scopes[-1]
        )
        return self.scopes[-1][name]

    def store(self, name, value):
        self.event('store', name,
            self.scopes[-1].get(name, 'undefined'), value
        )
        self.scopes[-1][name] = value


class Interpreter(EventProducer):
    def __init__(self, program, scanner, listeners=None):
        self.listeners = listeners
        self.program = program
        self.scanner = scanner
        self.context = Context(listeners=self.listeners)

    def __repr__(self):
        return "Interpreter(%r, %r, %r)" % (
            self.program, self.scanner, self.context
        )

    ### grammar stuff ---------------------------------------- ###
    
    def find_productions(self, name):
        productions = []
        for ast in self.program[1]:
            if ast[1] == name:
                productions.append(ast)
        if not productions:
            raise ValueError("No '%s' production defined" % name)
        return productions

    ### term matching ---------------------------------------- ###
    
    def match_all(self, patterns, values):
        """Returns a dict of bindings if all values match all patterns,
        or False if there was a mismatch.

        """
        i = 0
        bindings = {}
        while i < len(patterns):
            sub = self.match_terms(patterns[i], values[i])
            if sub == False:
                return False
            bindings.update(sub)
            i += 1
        return bindings
    
    def match_terms(self, pattern, value):
        """Returns a dict of bindings if the values matches the pattern,
        or False if there was a mismatch.

        """
        if isinstance(pattern, Variable):
            # TODO: check existing binding!  oh well, assume unique for now.
            return {pattern.name: value}
        elif isinstance(pattern, Term):
            i = 0
            if pattern.name != value.name:
                return False
            bindings = {}
            while i < len(pattern.contents):
                b = self.match_terms(pattern.contents[i], value.contents[i])
                if b == False:
                    return False
                bindings.update(b)
                i += 1
            return bindings

    ### interpreter proper ---------------------------------- ###
    
    def interpret(self, ast, bindings=None):
        """Returns a pair (bool, result) where bool is True if it
        succeeded and False if it failed.

        """
        self.event('interpret_ast', ast)
        if ast[0] == 'PROGRAM':
            mains = self.find_productions('main')
            return self.interpret(mains[0])
        elif ast[0] == 'PROD':
            self.context.push_scope(ast[1])
            if bindings:
                for name in bindings.keys():
                    self.context.store(name, bindings[name])
            self.event('begin_interpret_rule', ast[3])
            (succeeded, x) = self.interpret(ast[3])
            self.event('end_interpret_rule', ast[3])
            self.context.pop_scope(ast[1])
            return (succeeded, x)
        elif ast[0] == 'CALL':
            name = ast[1]
            args = ast[2]
            ibuf = ast[3]
            prods = self.find_productions(name)
            self.event('call_candidates', prods)
            args = [x.expand(self.context) for x in args]
            for prod in prods:
                formals = prod[2]
                self.event('call_args', formals, args)
                if isinstance(formals, list):
                    bindings = self.match_all(formals, args)
                    self.event('call_bindings', bindings)
                    if bindings != False:
                        if ibuf is not None:
                            return self.interpret_on_buffer(
                                prod, str(ibuf.expand(self.context)),
                                bindings=bindings
                            )
                        else:
                            return self.interpret(prod, bindings=bindings)
                else:
                    self.event('call_newfangled_parsing_args', prod)
                    # XXX bindings may happen as a result of this;
                    # they'll be in the interpreter's context?
                    (success, result) = self.interpret_on_buffer(
                        formals, str(args[0])
                    )
                    if success:
                        return self.interpret(prod)
            raise ValueError("No '%s' production matched arguments %r" %
                (name, args)
            )
        elif ast[0] == 'SEND':
            (success, result) = self.interpret(ast[1])
            assert isinstance(ast[2], Variable), ast
            self.context.store(ast[2].name, result)
            return (success, result)
        elif ast[0] == 'SET':
            assert isinstance(ast[1], Variable), ast
            assert isinstance(ast[2], Term), ast
            result = ast[2].expand(self.context)
            self.context.store(ast[1].name, result)
            return (True, result)
        elif ast[0] == 'AND':
            lhs = ast[1]
            rhs = ast[2]
            (succeeded, value_lhs) = self.interpret(lhs)
            if not succeeded:
                return (False, value_lhs)
            (succeeded, value_rhs) = self.interpret(rhs)
            return (succeeded, value_rhs)
        elif ast[0] == 'OR':
            lhs = ast[1]
            rhs = ast[2]
            saved_context = self.context.clone()
            saved_scanner_state = self.scanner.get_state()
            self.event('begin_or', lhs, rhs, saved_context, saved_scanner_state)
            (succeeded, result) = self.interpret(lhs)
            if succeeded:
                self.event('succeed_or', result)
                return (True, result)
            else:
                self.event('fail_or', self.context, self.scanner, result)
                self.context = saved_context
                self.scanner.install_state(saved_scanner_state)
                return self.interpret(rhs)
        elif ast[0] == 'RETURN':
            return (True, ast[1].expand(self.context))
        elif ast[0] == 'FAIL':
            return (False, ast[1].expand(self.context))
        elif ast[0] == 'EOF':
            if self.scanner.eof():
                return (True, EOF)
            else:
                return (False, Term("expected EOF found '%s'" %
                                    self.scanner.peek())
                       )
        elif ast[0] == 'PRINT':
            val = ast[1].expand(self.context)
            print val
            return (True, val)
        elif ast[0] == 'USING':
            sub = ast[1]
            scanner_name = ast[2]
            if scanner_name == u'tamsin':
                new_engine = TamsinScannerEngine()
            elif scanner_name == u'char':
                new_engine = CharScannerEngine()
            else:
                prods = self.find_productions(scanner_name)
                if len(prods) != 1:
                    raise ValueError("No such scanner '%s'" % scanner_name)
                new_engine = ProductionScannerEngine(self, prods[0])
            self.scanner.push_engine(new_engine)
            self.event('enter_with')
            (succeeded, result) = self.interpret(sub)
            self.event('leave_with', succeeded, result)
            self.scanner.pop_engine()
            return (succeeded, result)
        elif ast[0] == 'WHILE':
            result = Term('nil')
            self.event('begin_while')
            succeeded = True
            successful_result = result
            while succeeded:
                saved_context = self.context.clone()
                saved_scanner_state = self.scanner.get_state()
                (succeeded, result) = self.interpret(ast[1])
                if succeeded:
                    successful_result = result
                    self.event('repeating_while', result)
            self.context = saved_context
            self.scanner.install_state(saved_scanner_state)
            self.event('end_while', result)
            return (True, successful_result)
        elif ast[0] == 'LITERAL':
            upcoming_token = self.scanner.peek()
            self.event('try_literal', ast[1], self.scanner, upcoming_token)
            if self.scanner.consume(ast[1]):
                self.event('consume_literal', ast[1], self.scanner)
                return (True, Term(ast[1]))
            else:
                self.event('fail_literal', ast[1], self.scanner)
                s = ("expected '%s' found '%s' (at '%s')" %
                     (ast[1], upcoming_token,
                      self.scanner.report_buffer(self.scanner.position, 20)))
                return (False, Term(s))
        elif ast[0] == 'EXPECT':
            upcoming_token = self.scanner.peek()
            term = ast[1].expand(self.context)
            token = str(term)
            if self.scanner.consume(token):
                return (True, term)
            else:
                self.event('fail_term', ast[1], self.scanner)
                s = ("expected '%s' found '%s' (at '%s')" %
                     (token, upcoming_token,
                      self.scanner.report_buffer(self.scanner.position, 20)))
                return (False, Term(s))
        elif ast[0] == 'ANY':
            return (True, self.scanner.consume_any())
        else:
            raise NotImplementedError(repr(ast))

    def interpret_on_buffer(self, ast, buffer, bindings=None):
        self.event('interpret_on_buffer', buffer)
        saved_scanner_state = self.scanner.get_state()
        self.scanner.buffer = buffer
        self.scanner.position = 0
        self.scanner.reset_position = 0
        result = self.interpret(ast, bindings=bindings)
        self.scanner.install_state(saved_scanner_state)
        return result


def test_peek_is_idempotent():
    ast = ('PROGRAM', [('PROD', u'main', [], ('USING', ('CALL', u'program', [], None), u'scanner')), ('PROD', u'scanner', [], ('USING', ('CALL', u'scan', [], None), u'char')), ('PROD', u'scan', [], ('AND', ('LITERAL', u'X'), ('OR', ('AND', ('AND', ('AND', ('LITERAL', u'c'), ('LITERAL', u'a')), ('LITERAL', u't')), ('RETURN', Term('cat'))), ('AND', ('AND', ('AND', ('LITERAL', u'd'), ('LITERAL', u'o')), ('LITERAL', u'g')), ('RETURN', Term('dog')))))), ('PROD', u'program', [], ('AND', ('LITERAL', u'cat'), ('LITERAL', u'dog')))])
    scanner = Scanner('XdogXcat')
    scanner.push_engine(TamsinScannerEngine())
    interpreter = Interpreter(ast, scanner)
    
    prod = interpreter.find_productions('scanner')[0]
    print repr(prod)

    new_engine = ProductionScannerEngine(interpreter, prod)
    scanner.push_engine(new_engine)
    
    print "---INITIAL STATE---"
    scanner.dump()
    print repr(interpreter)
    print

    print "---INITIAL CALL TO peek---"
    token = scanner.peek()
    print token
    scanner.dump()
    print repr(interpreter)
    print

    for i in xrange(0, 4):
        sav_tok = token
        print "---SUBSEQUENT CALL TO peek---"
        token = scanner.peek()
        print token
        scanner.dump()
        print repr(interpreter)
        print

        if sav_tok != token:
            print "FAILED"
            break


def main(args):
    debug = None
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
    if args[0] == 'test':
        test_peek_is_idempotent()
        return
    if args[0] == 'parse':
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            print repr(ast)
    elif args[0] == 'run':
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents, listeners=listeners)
            ast = parser.grammar()
            #print repr(ast)
            scanner = Scanner(sys.stdin.read(), listeners=listeners)
            scanner.push_engine(TamsinScannerEngine())
            interpreter = Interpreter(
                ast, scanner, listeners=listeners
            )
            (succeeded, result) = interpreter.interpret(ast)
            if not succeeded:
                sys.stderr.write(str(result) + "\n")
                sys.exit(1)
            print str(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")


if __name__ == '__main__':
    main(sys.argv[1:])
