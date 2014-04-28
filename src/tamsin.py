#!/usr/bin/env python
# encoding: UTF-8

import codecs
import sys


def enc(x):
    if not isinstance(x, str):
        x = unicode(x)
    return x.encode('ascii', 'xmlcharrefreplace')


class TamsinParseError(ValueError):
    pass


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
        if not getattr(self, 'listeners', None):
            self.listeners = []
        for listener in self.listeners:
            listener.announce(tag, *data)

    def subscribe(self, listener):
        if not getattr(self, 'listeners', None):
            self.listeners = []
        self.listeners.append(listener)


class DebugEventListener(object):
    def listen_to(self, producer):
        producer.subscribe(self)
    
    def announce(self, tag, *data):
        if tag in (): # ('interpret_ast', 'try_literal'):
            return
        elif tag in ('switched_scanner_forward', 'switched_scanner_back'):
            print tag
            data[0].dump()
            data[1].dump()
        else:
            print "%s %r" % (tag, data)


class Scanner(EventProducer):
    def __init__(self, buffer):
        """Does NOT calls scan() for you.  You should do that before
        using it.

        """
        self.event('set_buffer', buffer)
        self.buffer = buffer
        self.position = 0
        self.reset_position = 0
        self.token = None

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
        raise ValueError(u"Expected %s, found '%s' at '%s...' (position %s)" %
                         (enc(expected),
                          enc(self.token),
                          self.report_buffer(self.position, 20),
                          self.position))

    def clone(self):
        n = self.__class__(self.buffer)
        n.position = self.position
        n.reset_position = self.reset_position
        n.token = self.token
        return n

    def scan(self):
        self.reset_position = self.position
        self.scan_impl()
        self.event('scanned', self)

    def switch(self, new_scanner):
        """Returns the new_scanner for convenience.

        """
        self.event('switch_scanner', self, new_scanner)
        # 'putback' the token
        self.position = self.reset_position
        self.reset_position = 0
        self.token = None
        # copy properties over to new scanner
        new_scanner.position = self.position
        new_scanner.reset_position = 0
        new_scanner.token = None
        # prime the pump
        new_scanner.scan()
        self.event('switched_scanner', new_scanner)
        return new_scanner

    def consume(self, t):
        self.event('consume', t)
        if self.token == t:
            self.scan()
            return t
        else:
            return None
    
    def expect(self, t):
        r = self.consume(t)
        if r is None:
            self.error("'%s'" % t)
        return r
    
    def dump(self):
        print "--%r" % self
        print "  buffer: %s" % enc(self.buffer)
        print "  position: %s" % self.position
        print "  buffer at position: %s" % self.report_buffer(self.position, 40)
        print "  reset_position: %s" % self.reset_position
        print "  buffer at reset_pos: %s" % self.report_buffer(self.reset_position, 40)
        print "  token: %s" % enc(self.token)


class TamsinScanner(Scanner):
    def scan_impl(self):
        while self.startswith((' ', '\t', '\r', '\n')):
            self.chop(1)

        if self.eof():
            self.token = None
            return

        if self.startswith(('&&', '||')):
            self.token = self.chop(1)
            self.chop(1)
            return
        
        if self.startswith(('=', '(', ')', '[', ']', '{', '}',
                            '|', '&', u'→', ',', '.', '@', u'•')):
            self.token = self.chop(1)
            return

        if self.startswith(('"',)):
            self.token = '"'
            self.chop(1)
            while not self.eof() and not self.startswith('"'):
                self.token += self.chop(1)
            self.chop(1)  # chop ending quote
            return

        if self.startswith((u'「',)):
            self.token = u'「'
            self.chop(1)
            while not self.eof() and not self.startswith(u'」'):
                self.token += self.chop(1)
            self.chop(1)  # chop ending quote
            return

        if not self.eof() and self.isalnum():
            self.token = ''
            while not self.eof() and self.isalnum():
                self.token += self.chop(1)
            return

        self.token = self.buffer[0]
        self.error('identifiable character')


class RawScanner(Scanner):
    def scan_impl(self):
        if self.eof():
            self.token = None
            return
        self.token = self.chop(1)


class ProductionScanner(Scanner):
    """A Scanner that uses a production of the Tamsin program to
    scan the input.

    """
    def __init__(self, buffer, interpreter, production):
        Scanner.__init__(self, buffer)
        self.interpreter = interpreter
        self.production = production

    def clone(self):
        n = self.__class__(self.buffer, self.interpreter, self.production)
        n.position = self.position
        n.reset_position = self.reset_position
        n.token = self.token
        return n

    def scan_impl(self):
        if self.eof():
            self.token = None
            return
        self.token = str(self.interpreter.interpret(self.production))
        self.event('production_scan', self.production, self.token)


class Parser(EventProducer):
    def __init__(self, buffer):
        self.scanner = TamsinScanner(buffer)
        self.scanner.scan()

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
    def scan(self):
        return self.scanner.scan()
    def consume(self, t):
        return self.scanner.consume(t)
    def expect(self, t):
        return self.scanner.expect(t)

    def grammar(self):
        prods = [self.production()]
        while self.scanner.token is not None:
            prods.append(self.production())
        
        return ('PROGRAM', prods)
    
    def production(self):
        name = self.scanner.token
        self.scan()
        args = []
        if self.consume('('):
            if self.scanner.token != ')':
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
            scanner_name = self.scanner.token
            self.scan()
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
        elif self.scanner.token and self.scanner.token[0] == '"':
            literal = self.scanner.token[1:]
            self.scan()
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
        elif self.consume('print'):
            t = self.term()
            return ('PRINT', t)
        else:
            name = self.scanner.token
            self.scan()
            args = []
            if self.consume('('):
                if self.scanner.token != ')':
                    args.append(self.term())
                    while self.consume(','):
                        args.append(self.term())
                self.expect(')')
            ibuf = None
            if self.consume('@'):
                ibuf = self.term()
            return ('CALL', name, args, ibuf)

    def variable(self):
        if self.scanner.token[0].isupper():
            var = self.scanner.token
            self.scan()
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
        if self.scanner.token[0].isupper():
            return self.variable()
        elif self.scanner.token[0].isalnum() or self.scanner.token[0] == u'「':
            atom = self.scanner.token
            if atom[0] == u'「':
                atom = atom[1:]
            self.scan()
            subs = []
            if self.consume('('):
                if self.scanner.token != ')':
                    subs.append(self.term())
                while self.consume(','):
                    subs.append(self.term())
                self.expect(')')
            return Term(atom, subs)
        else:
            self.error('term')


class Context(EventProducer):
    def __init__(self):
        self.scopes = []

    def push_scope(self, purpose):
        self.scopes.append({})
        self.event('push_scope', self)

    def pop_scope(self, purpose):
        self.scopes.pop()
        self.event('pop_scope', self)

    def clone(self):
        n = Context()
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
    def __init__(self, ast, buffer):
        self.program = ast
        self.scanner = TamsinScanner(buffer)
        self.scanner.scan()
        self.context = Context()

    ### grammar stuff ---------------------------------------- ###
    
    def find_productions(self, name):
        productions = []
        for ast in self.program[1]:
            if ast[1] == name:
                productions.append(ast)
        if not productions:
            raise ValueError("No '%s' production defined" % name)
        return productions

    ### term matching
    
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
            x = self.interpret(ast[3])
            self.event('end_interpret_rule', ast[3])
            self.context.pop_scope(ast[1])
            return x
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
                            self.scanner.token = None
                            self.scanner.scan()
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
            result = self.interpret(ast[1])
            assert isinstance(ast[2], Variable), ast
            self.context.store(ast[2].name, result)
            return result
        elif ast[0] == 'SET':
            assert isinstance(ast[1], Variable), ast
            assert isinstance(ast[2], Term), ast
            result = ast[2].expand(self.context)
            self.context.store(ast[1].name, result)
            return result
        elif ast[0] == 'AND':
            lhs = ast[1]
            rhs = ast[2]
            value_lhs = self.interpret(lhs)
            value_rhs = self.interpret(rhs)
            return value_rhs
        elif ast[0] == 'OR':
            lhs = ast[1]
            rhs = ast[2]
            saved_context = self.context.clone()
            saved_scanner = self.scanner.clone()
            try:
                return self.interpret(lhs)
            except TamsinParseError as e:
                self.context = saved_context
                self.scanner = saved_scanner
                return self.interpret(rhs)
        elif ast[0] == 'RETURN':
            return ast[1].expand(self.context)
        elif ast[0] == 'FAIL':
            raise TamsinParseError("fail")
        elif ast[0] == 'PRINT':
            val = ast[1].expand(self.context)
            print val
            return val
        elif ast[0] == 'WITH':
            sub = ast[1]
            scanner_name = ast[2]
            if scanner_name == u'tamsin':
                new_scanner = TamsinScanner(self.scanner.buffer)
            elif scanner_name == u'raw':
                new_scanner = RawScanner(self.scanner.buffer)
            else:
                prods = self.find_productions(scanner_name)
                if len(prods) != 1:
                    raise ValueError("No such scanner '%s'" % scanner_name)
                new_scanner = ProductionScanner(
                    self.scanner.buffer, self, prods[0]
                )
            self.event("switching_scanners")
            old_scanner = self.scanner
            self.scanner = self.scanner.switch(new_scanner)
            self.event("switched_scanner_forward", old_scanner, self.scanner)
            result = self.interpret(sub)
            prev_scanner = self.scanner
            self.scanner = self.scanner.switch(old_scanner)
            self.event("switched_scanner_back", prev_scanner, self.scanner)
            return result
        elif ast[0] == 'WHILE':
            result = Term('nil')
            while True:
                saved_context = self.context.clone()
                saved_scanner = self.scanner.clone()
                try:
                    result = self.interpret(ast[1])
                except TamsinParseError as e:
                    self.context = saved_context
                    self.scanner = saved_scanner
                    return result
        elif ast[0] == 'LITERAL':
            self.event('try_literal', ast[1], self.scanner.token)
            if self.scanner.token == ast[1]:
                self.scanner.scan()
                return Term(ast[1])
            else:
                raise TamsinParseError("expected '%s' found '%s'" %
                    (ast[1], self.scanner.token)
                )
        else:
            raise NotImplementedError(repr(ast))


def main(args):
    debug = None
    if args[0] == '--debug':
        debug = DebugEventListener()
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
            parser = Parser(contents)
            if debug:
                debug.listen_to(parser)
            ast = parser.grammar()
            #print repr(ast)
            interpreter = Interpreter(ast, sys.stdin.read())
            if debug:
                debug.listen_to(interpreter)
            result = interpreter.interpret(ast)
            print str(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")


if __name__ == '__main__':
    main(sys.argv[1:])
