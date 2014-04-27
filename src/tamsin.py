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
        raise ValueError("Expected %s, found '%s' at '%s...'" %
                         (expected, self.token, self.buffer[:20]))

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
        #print repr(self.input)
    
    def scan(self):
        if self.position >= len(self.input):
            self.token = None
        else:
            self.token = self.input[self.position]
            self.position += 1

    def rewind(self, position):
        self.position = position
        self.token = self.input[position - 1]

    def find_production(self, name):
        found = None
        for x in self.program[1]:
            if x[1] == name:
                found = x
                break
        if not found:
            raise ValueError("No '%s' production defined" % name)
        return found

    def replace_vars(self, ast, context):
        """Expands a term."""
        
        if ast[0] == 'ATOM':
            return ast
        elif ast[0] == 'LIST':
            return ('LIST', [self.replace_vars(x, context) for x in ast[1]])
        elif ast[0] == 'VAR':
            return context[ast[1]] # context.get(ast[1], None)
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

    def interpret(self, ast, context):
        if ast[0] == 'PROGRAM':
            return self.interpret(self.find_production('main'), context)
        elif ast[0] == 'PROD':
            #print "interpreting %s" % repr(ast)
            return self.interpret(ast[2], {})
        elif ast[0] == 'CALL':
            new_context = {}
            result = self.interpret(self.find_production(ast[1]), new_context)
            if ast[2] is not None:
                assert ast[2][0] == 'VAR', ast
                varname = ast[2][1]
                debug("updating %s (was %s) to %r" %
                    (varname, context.get(varname, 'undefined'), result)
                )
                context[varname] = result
            return result
        elif ast[0] == 'SET':
            assert ast[1][0] == 'VAR', ast
            varname = ast[1][1]
            result = self.replace_vars(ast[2], context)
            debug("setting %s (was %s) to %r" %
                (varname, context.get(varname, 'undefined'), result)
            )
            context[varname] = result
            return result
        elif ast[0] == 'AND':
            lhs = ast[1]
            rhs = ast[2]
            value_lhs = self.interpret(lhs, context)
            value_rhs = self.interpret(rhs, context)
            return value_rhs
        elif ast[0] == 'OR':
            lhs = ast[1]
            rhs = ast[2]
            saved_context = context.copy()
            saved_position = self.position
            try:
                return self.interpret(lhs, context)
            except TamsinParseError as e:
                context = saved_context
                self.rewind(saved_position)
                return self.interpret(rhs, context)
        elif ast[0] == 'RETURN':
            return self.replace_vars(ast[1], context)
        elif ast[0] == 'FAIL':
            raise TamsinParseError("fail")
        elif ast[0] == 'WHILE':
            result = ('ATOM', 'nil')
            while True:
                try:
                    result = self.interpret(ast[1], context)
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


if __name__ == '__main__':
    if sys.argv[1] == 'parse':
        with codecs.open(sys.argv[2], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            print repr(ast)
    elif sys.argv[1] == 'run':
        with codecs.open(sys.argv[2], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            #print repr(ast)
            interpreter = Interpreter(ast, sys.stdin.read())
            result = interpreter.interpret(ast, {})
            print interpreter.stringify_term(result)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")
