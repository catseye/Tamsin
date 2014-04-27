#!/usr/bin/env python
# encoding: UTF-8

import codecs
import sys

DEBUG = False

def debug(x):
    if DEBUG:
        print x

class TamsinParseError(ValueError):
    pass

class Parser(object):

    def __init__(self, buffer):
        self.buffer = buffer
        self.token = None
        self.position = 0
        self.scan()

    ### scanner bits first

    def chop(self, amount):
        result = self.buffer[:amount]
        self.buffer = self.buffer[amount:]
        self.position += amount
        return result

    def error(self, expected):
        report = self.buffer[:20]
        if len(self.buffer) > 20:
            report += '...'
        raise ValueError("Expected %s, found '%s' at '%s...'" %
                         (expected, self.token, report))

    def scan(self):
        self.scan_impl()
        #print "scanned: '%s'" % self.token

    def scan_impl(self):
        while self.buffer.startswith((' ', '\t', '\r', '\n')):
            self.chop(1)

        if self.buffer.startswith(('&&', '||')):
            self.token = self.chop(1)
            self.chop(1)
            return
        
        if self.buffer.startswith(('=', '(', ')', '[', ']', '{', '}',
                                   '|', '&', u'→', '.')):
            self.token = self.chop(1)
            return

        if self.buffer.startswith('"'):
            self.token = '"'
            self.chop(1)
            while self.buffer and not self.buffer.startswith('"'):
                self.token += self.chop(1)
            self.chop(1)  # chop ending quote
            return
        
        for keyword in ('set', 'return', 'fail'):
            if self.buffer.startswith(keyword):
                self.token = self.chop(len(keyword))
                return

        if self.buffer and self.buffer[0].isalpha():
            self.token = ''
            while self.buffer and self.buffer[0].isalpha():
                self.token += self.chop(1)
            return

        if not self.buffer:
            self.token = None
            return

        self.token = self.buffer[0]
        self.error('identifiable character')
        
    def consume(self, t):
        #print repr(self.token), repr(t)
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

    ### now the parser bits

    def grammar(self):
        prods = [self.production()]
        while self.token is not None:
            prods.append(self.production())
        
        return ('PROGRAM', prods)
    
    def production(self):
        name = self.token
        self.scan()
        self.expect('=')
        e = self.expr0()
        self.expect('.')
        return ('PROD', name, e)
    
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
        if self.consume('('):
            e = self.expr0()
            self.expect(')')
            return e
        elif self.consume('['):
            e = self.expr0()
            self.expect(']')
            return ('OR', e, ('RETURN', ('ATOM', u'nil')))
        elif self.consume('{'):
            e = self.expr0()
            self.expect('}')
            return ('WHILE', e)
        elif self.token and self.token[0] == '"':
            literal = self.token[1:]
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
        else:
            t = self.token
            self.scan()
            v = None
            if self.consume(u'→'):
                v = self.variable()
            return ('CALL', t, v)

    def variable(self):
        if self.token[0].isupper():
            var = self.token
            self.scan()
            return ('VAR', var)
        else:
            raise ValueError("Expected variable")

    def term(self):
        if self.consume('('):
            subs = []
            while (self.token != ')'):
                subs.append(self.term())
            self.expect(')')
            return ('LIST', subs)
        elif self.token[0].isupper():
            return self.variable()
        else:
            atom = self.token
            self.scan()
            return ('ATOM', atom)


class Interpreter(object):
    def __init__(self, ast, input_):
        self.program = ast
        self.input = input_.split(' ')
        self.position = 0
        self.scan()
        self.contexts = []
        #print repr(self.input)

    ### context stuff ---------------------------------------- ###
    
    def push_context(self, purpose):
        debug("pushing new context for %r" % purpose)
        self.contexts.append({})

    def pop_context(self, purpose):
        debug("popping context for %r" % purpose)
        self.contexts.pop()

    def current_context(self):
        """Don't assume anything about what this returns except that
        you can pass it to install_context().

        """
        debug("retrieving current context %r" % self.contexts[-1])
        return self.contexts[-1].copy()

    def install_context(self, context):
        debug("installing context %r" % context)
        self.contexts[-1] = context

    def fetch(self, name):
        debug("fetching %s (it's %r)" %
            (name, self.contexts[-1].get(name, 'undefined'))
        )
        return self.contexts[-1][name]

    def store(self, name, value):
        debug("updating %s (was %s) to %r" %
            (name, self.contexts[-1].get(name, 'undefined'), value)
        )
        self.contexts[-1][name] = value

    ### scanner stuff ---------------------------------------- ###
    
    def scan(self):
        if self.position >= len(self.input):
            self.token = None
        else:
            self.token = self.input[self.position]
            self.position += 1

    def rewind(self, position):
        self.position = position
        self.token = self.input[position - 1]

    ### grammar stuff ---------------------------------------- ###
    
    def find_production(self, name):
        found = None
        for x in self.program[1]:
            if x[1] == name:
                found = x
                break
        if not found:
            raise ValueError("No '%s' production defined" % name)
        return found

    ### term stuff ---------------------------------------- ###
    
    def replace_vars(self, ast):
        """Expands a term, replacing all (VAR x) with the value of x
        in the current context."""
        
        if ast[0] == 'ATOM':
            return ast
        elif ast[0] == 'LIST':
            return ('LIST', [self.replace_vars(x) for x in ast[1]])
        elif ast[0] == 'VAR':
            return self.fetch(ast[1])
        else:
            raise NotImplementedError("internal error: bad term")

    def stringify_term(self, ast):
        if ast[0] == 'ATOM':
            return ast[1]
        elif ast[0] == 'LIST':
            return '(%s)' % ' '.join([self.stringify_term(x) for x in ast[1]])
        elif ast[0] == 'VAR':
            return ast[1]
        else:
            raise NotImplementedError("internal error: bad term")

    ### interpreter proper ---------------------------------- ###
    
    def interpret(self, ast):
        if ast[0] == 'PROGRAM':
            return self.interpret(self.find_production('main'))
        elif ast[0] == 'PROD':
            #print "interpreting %s" % repr(ast)
            self.push_context(ast[1])
            x = self.interpret(ast[2])
            self.pop_context(ast[1])
            return x
        elif ast[0] == 'CALL':
            result = self.interpret(self.find_production(ast[1]))
            if ast[2] is not None:
                assert ast[2][0] == 'VAR', ast
                varname = ast[2][1]
                self.store(varname, result)
            return result
        elif ast[0] == 'SET':
            assert ast[1][0] == 'VAR', ast
            varname = ast[1][1]
            result = self.replace_vars(ast[2])
            self.store(varname, result)
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
            saved_context = self.current_context()
            saved_position = self.position
            try:
                return self.interpret(lhs)
            except TamsinParseError as e:
                self.install_context(saved_context)
                self.rewind(saved_position)
                return self.interpret(rhs)
        elif ast[0] == 'RETURN':
            return self.replace_vars(ast[1])
        elif ast[0] == 'FAIL':
            raise TamsinParseError("fail")
        elif ast[0] == 'WHILE':
            result = ('ATOM', 'nil')
            while True:
                try:
                    result = self.interpret(ast[1])
                except TamsinParseError as e:
                    return result
        elif ast[0] == 'LITERAL':
            if self.token == ast[1]:
                self.scan()
                return ('ATOM', ast[1])
            else:
                raise TamsinParseError("expected '%s' found '%s'" %
                    (ast[1], self.token)
                )
        else:
            raise NotImplementedError(repr(ast))


def main(args):
    global DEBUG
    if args[0] == '--debug':
        DEBUG = True
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
            ast = parser.grammar()
            #print repr(ast)
            interpreter = Interpreter(ast, sys.stdin.read())
            result = interpreter.interpret(ast)
            print interpreter.stringify_term(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")


if __name__ == '__main__':
    main(sys.argv[1:])
