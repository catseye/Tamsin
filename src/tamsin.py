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
        self.position = position
        self.reset_position = position

    def set_interpreter(self, interpreter):
        # ignored by all but ProductionScanner
        pass

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
        raise ValueError(u"Expected %s' at '%s...' (position %s)" %
                         (enc(expected),
                          self.report_buffer(self.position, 20),
                          self.position))

    def clone(self):
        assert self.position == self.reset_position, "divergent..."
        return self.__class__(self.buffer, position=self.position,
                              listeners=self.listeners)

    def scan(self):
        """Returns the next token from the buffer.
        
        You MUST call either commit() or unscan() after calling this,
        as otherwise the position and reset_position will be divergent
        (and you will trigger an assert if you try to scan() or clone().)
        If you want to just see what the next token would be, call next_tok().

        """
        assert self.position == self.reset_position, "divergent..."
        tok = self.scan_impl()
        self.event('scanned', self, tok)
        return tok

    def unscan(self):
        self.position = self.reset_position

    def commit(self):
        self.reset_position = self.position

    def next_tok(self):
        tok = self.scan()
        self.unscan()
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
        print "--" * indent + "buffer: '%s'" % enc(self.buffer)
        print "--" * indent + "position: %s" % self.position
        print "--" * indent + "buffer at position: '%s'" % self.report_buffer(self.position, 40)
        print "--" * indent + "reset_position: %s" % self.reset_position
        print "--" * indent + "buffer at reset_pos: '%s'" % self.report_buffer(self.reset_position, 40)


class TamsinScanner(Scanner):
    def scan_impl(self):
        while self.startswith((' ', '\t', '\r', '\n')):
            self.chop(1)

        if self.eof():
            return EOF

        if self.startswith(('&&', '||')):
            tok = self.chop(1)
            self.chop(1)
            return tok
        
        if self.startswith(('=', '(', ')', '[', ']', '{', '}',
                            '|', '&', u'→', ',', '.', '@', u'•', u'□')):
            return self.chop(1)

        if self.startswith(('"',)):
            tok = '"'
            self.chop(1)
            while not self.eof() and not self.startswith('"'):
                tok += self.chop(1)
            self.chop(1)  # chop ending quote
            return tok

        if self.startswith((u'「',)):
            tok = u'「'
            self.chop(1)
            while not self.eof() and not self.startswith(u'」'):
                tok += self.chop(1)
            self.chop(1)  # chop ending quote
            return tok

        if not self.eof() and self.isalnum():
            tok = ''
            while not self.eof() and self.isalnum():
                tok += self.chop(1)
            return tok

        self.error('identifiable character')


class RawScanner(Scanner):
    def scan_impl(self):
        if self.eof():
            return EOF
        return self.chop(1)


class ProductionScanner(Scanner):
    """A Scanner that uses a production of the Tamsin program to
    scan the input.
    
    Uses its own Interpreter.  Let's see if that helps.

    """
    def __init__(self, buffer, production, position=0, listeners=None):
        Scanner.__init__(
            self, buffer, position=position, listeners=listeners
        )
        self.interpreter = None
        self.production = production

    def set_interpreter(self, interpreter):
        self.interpreter = interpreter

    def clone(self):
        assert self.position == self.reset_position, "divergent..."
        n = self.__class__(
            self.buffer, self.production, position=self.position,
            listeners=self.listeners
        )
        n.set_interpreter(self.interpreter)
        return n

    def scan_impl(self):
        if self.eof():
            return EOF
        # if we ever go back to exceptions, we would have a try/catch here
        (success, tok) = self.interpreter.interpret(self.production)
        if success:
            self.event('production_scan', self.production, tok)
            return str(tok)
        else:
            return EOF


class Parser(EventProducer):
    def __init__(self, buffer, listeners=None):
        self.listeners = listeners
        self.scanner = TamsinScanner(buffer, listeners=self.listeners)

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
    def next_tok(self):
        return self.scanner.next_tok()
    def consume(self, t):
        return self.scanner.consume(t)
    def consume_any(self):
        return self.scanner.consume_any()
    def expect(self, t):
        return self.scanner.expect(t)

    def grammar(self):
        prods = [self.production()]
        while self.next_tok() is not EOF:
            prods.append(self.production())
        return ('PROGRAM', prods)

    def production(self):
        name = self.consume_any()
        args = []
        if self.consume('('):
            if self.next_tok() != ')':
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
        if self.consume('with'):
            scanner_name = self.consume_any()
            lhs = ('WITH', lhs, scanner_name)
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
        elif (self.scanner.next_tok() is not None and
              self.scanner.next_tok()[0] == '"'):
            literal = self.consume_any()[1:]
            return ('LITERAL', literal)
        elif self.consume('set'):
            v = self.variable()
            self.expect("=")
            t = self.term()
            return ('SET', v, t)
        elif self.consume('return'):
            t = self.term()
            return ('RETURN', t)
        elif self.consume('fail'):
            return ('FAIL',)
        elif self.consume(u'□'):
            return ('EOF',)
        elif self.consume('print'):
            t = self.term()
            return ('PRINT', t)
        else:
            name = self.consume_any()
            args = []
            if self.consume('('):
                if self.scanner.next_tok() != ')':
                    args.append(self.term())
                    while self.consume(','):
                        args.append(self.term())
                self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.term()
            return ('CALL', name, args, ibuf)

    def variable(self):
        if self.scanner.next_tok()[0].isupper():
            var = self.consume_any()
            return Variable(var)
        else:
            self.error('variable')

    def term(self):
        lhs = self.term1()
        while self.consume(u'•'):
            rhs = self.term1()
            lhs = Concat(lhs, rhs)
        return lhs

    def term1(self):
        if self.scanner.next_tok()[0].isupper():
            return self.variable()
        elif (self.scanner.next_tok()[0].isalnum() or
              self.scanner.next_tok()[0][0] == u'「'):
            atom = self.consume_any()
            if atom[0] == u'「':
                atom = atom[1:]
            subs = []
            if self.consume('('):
                if self.scanner.next_tok() != ')':
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
    def __init__(self, ast, scanner, listeners=None):
        self.listeners = listeners
        self.program = ast
        self.scanner = scanner
        self.scanner.set_interpreter(self)
        self.context = Context(listeners=self.listeners)

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
                        saved_scanner_state = None
                        if ibuf is not None:
                            ibuf = ibuf.expand(self.context)
                            self.event('call_ibuf', ibuf)
                            saved_scanner = self.scanner
                            self.scanner = self.scanner.clone()
                            self.scanner.buffer = str(ibuf)
                            self.scanner.position = 0
                            self.scanner.saved_position = 0
                        x = self.interpret(prod, bindings=bindings)
                        if ibuf is not None:
                            self.scanner = saved_scanner
                        return x
                else:
                    self.event('call_newfangled_parsing_args', prod)
            raise ValueError("No '%s' production matched arguments %r" %
                (name, args)
            )
        elif ast[0] == 'SEND':
            (succeded, result) = self.interpret(ast[1])
            assert isinstance(ast[2], Variable), ast
            self.context.store(ast[2].name, result)
            return (succeded, result)
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
            saved_scanner = self.scanner.clone()
            self.event('begin_or', lhs, rhs, saved_context, saved_scanner)
            (succeeded, result) = self.interpret(lhs)
            if succeeded:
                self.event('succeed_or', result)
                return (True, result)
            else:
                self.event('fail_or', self.context, self.scanner, result)
                self.context = saved_context
                assert self.scanner.__class__ == saved_scanner.__class__
                self.scanner = saved_scanner
                return self.interpret(rhs)
        elif ast[0] == 'RETURN':
            return (True, ast[1].expand(self.context))
        elif ast[0] == 'FAIL':
            return (False, Term("fail"))
        elif ast[0] == 'EOF':
            if self.scanner.eof():
                return (True, EOF)
            else:
                return (False, Term("expected EOF found '%s'" %
                                    self.scanner.next_tok())
                       )
        elif ast[0] == 'PRINT':
            val = ast[1].expand(self.context)
            print val
            return (True, val)
        elif ast[0] == 'WITH':
            sub = ast[1]
            scanner_name = ast[2]
            interpreter_to_use = self
            if scanner_name == u'tamsin':
                new_scanner = TamsinScanner(self.scanner.buffer,
                    position=self.scanner.position,
                    listeners=self.listeners
                )
            elif scanner_name == u'raw':
                new_scanner = RawScanner(self.scanner.buffer,
                    position=self.scanner.position,
                    listeners=self.listeners
                )
            else:
                prods = self.find_productions(scanner_name)
                if len(prods) != 1:
                    raise ValueError("No such scanner '%s'" % scanner_name)
                new_scanner = ProductionScanner(
                    self.scanner.buffer, prods[0],
                    position=self.scanner.position,
                    listeners=self.listeners
                )
            new_interpreter = Interpreter(
                self.program, new_scanner, listeners=self.listeners
            )
            self.event('enter_interpreter', new_scanner, new_interpreter)
            (succeeded, result) = new_interpreter.interpret(sub)
            #print >>sys.stderr, succeeded, result
            self.event('leave_interpreter', self.scanner, self)
            assert new_scanner.position == new_scanner.reset_position
            self.scanner.position = new_scanner.position
            self.scanner.reset_position = self.scanner.position
            return (succeeded, result)
        elif ast[0] == 'WHILE':
            result = Term('nil')
            self.event('begin_while')
            succeeded = True
            successful_result = result
            while succeeded:
                saved_context = self.context.clone()
                saved_scanner = self.scanner.clone()
                (succeeded, result) = self.interpret(ast[1])
                if succeeded:
                    successful_result = result
                    self.event('repeating_while', result)
            self.context = saved_context
            assert self.scanner.__class__ == saved_scanner.__class__
            self.scanner = saved_scanner
            self.event('end_while', result)
            return (True, successful_result)
        elif ast[0] == 'LITERAL':
            self.event('try_literal', ast[1], self.scanner)
            if self.scanner.consume(ast[1]):
                self.event('consume_literal', ast[1], self.scanner)
                return (True, Term(ast[1]))
            else:
                self.event('fail_literal', ast[1], self.scanner)
                s = ("expected '%s' found '%s' (%r vs %r) (at '%s')" %
                     (ast[1], self.scanner.next_tok(),
                      ast[1], self.scanner.next_tok(),
                      self.scanner.report_buffer(self.scanner.position, 20)))
                return (False, Term(s))
        else:
            raise NotImplementedError(repr(ast))


def main(args):
    debug = None
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
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
            interpreter = Interpreter(
                ast,
                TamsinScanner(sys.stdin.read(), listeners=listeners),
                listeners=listeners
            )
            (succeeded, result) = interpreter.interpret(ast)
            if not succeeded:
                sys.stderr.write(str(result))
                sys.exit(1)
            print str(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")


if __name__ == '__main__':
    main(sys.argv[1:])
