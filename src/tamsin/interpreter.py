# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import sys

from tamsin.ast import (
    Module, Production, And, Or, Not, While, Call, Send, Set, Using,
    Prodref, Concat
)
from tamsin.term import Term, EOF, Atom, Constructor, Variable
from tamsin.event import EventProducer
from tamsin.scanner import (
    ByteScannerEngine, UTF8ScannerEngine, ProductionScannerEngine
)


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
        assert(isinstance(value, Term)), "not a Term: %r" % value
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

    ### interpreter proper ---------------------------------- ###

    def interpret_program(self, program):
        prods = program.find_productions(Prodref('main', 'main'))
        return self.interpret(prods[0])

    def interpret(self, ast, bindings=None):
        """Returns a pair (bool, result) where bool is True if it
        succeeded and False if it failed.

        """
        self.event('interpret_ast', ast)
        if isinstance(ast, Production):
            name = ast.name
            if name == '$.expect':
                upcoming_token = self.scanner.peek()
                term = bindings['X']
                token = str(term)
                if self.scanner.consume(token):
                    return (True, term)
                else:
                    self.event('fail_term', ast.name, self.scanner)
                    s = ("expected '%s' found '%s' (at '%s')" %
                         (token, upcoming_token,
                          self.scanner.report_buffer(self.scanner.position, 20)))
                    return (False, Atom(s))
            elif name == '$.return':
                return (True, bindings['X'])
            elif name == '$.eof':
                if self.scanner.peek() is EOF:
                    return (True, EOF)
                else:
                    return (False, Atom("expected EOF found '%s'" %
                            self.scanner.peek()))
            elif name == '$.any':
                if self.scanner.peek() is EOF:
                    return (False, Atom("expected any token, found EOF"))
                else:
                    return (True, Atom(self.scanner.consume_any()))
            elif name == '$.alnum':
                if (self.scanner.peek() is not EOF and
                    self.scanner.peek()[0].isalnum()):
                    return (True, Atom(self.scanner.consume_any()))
                else:
                    return (False, Atom("expected alphanumeric, found '%s'" %
                                        self.scanner.peek()))
            elif name == '$.upper':
                if (self.scanner.peek() is not EOF and
                    self.scanner.peek()[0].isupper()):
                    return (True, Atom(self.scanner.consume_any()))
                else:
                    return (False, Atom("expected uppercase alphabetic, found '%s'" %
                                        self.scanner.peek()))
            elif name == '$.startswith':
                if (self.scanner.peek() is not EOF and
                    self.scanner.peek()[0].startswith((str(bindings['X']),))):
                    return (True, Atom(self.scanner.consume_any()))
                else:
                    return (False, Atom("expected '%s, found '%s'" %
                                        (bindings['X'], self.scanner.peek())))
            elif name == '$.equal':
                if (isinstance(bindings['L'], Atom) and
                    isinstance(bindings['R'], Atom) and
                    bindings['L'].text == bindings['R'].text):
                    return (True, bindings['L'])
                else:
                    return (False, Atom("term '%s' does not equal '%s'" %
                                        (bindings['L'], bindings['R'])))
            elif name == '$.unquote':
                x = str(bindings['X'])
                if (x.startswith((str(bindings['L']),)) and
                    x.endswith((str(bindings['R']),))):
                    return (True, Atom(x[1:-1]))
                else:
                    return (False, Atom("term '%s' is not quoted with '%s' and '%s'" %
                                        (bindings['X'], bindings['L'], bindings['R'])))
            elif name == '$.mkterm':
                t = bindings['T']
                l = bindings['L']
                contents = []
                while isinstance(l, Constructor) and l.tag == 'list':
                    contents.append(l.contents[0])
                    l = l.contents[1]
                if contents:
                    return (True, Constructor(t.text, contents))
                else:
                    return (True, t)
            elif name == '$.print':
                val = bindings['X']
                sys.stdout.write(str(val))
                sys.stdout.write("\n")
                return (True, val)
            elif name == '$.emit':
                val = bindings['X']
                sys.stdout.write(str(val))
                return (True, val)
            elif name == '$.fail':
                return (False, bindings['X'])
            elif name.startswith('$.'):
                raise ValueError("No '%s' production defined" % name)
            self.context.push_scope(name)
            if bindings:
                for name in bindings.keys():
                    self.context.store(name, bindings[name])
            self.event('begin_interpret_rule', ast.body)
            (success, result) = self.interpret(ast.body)
            self.event('end_interpret_rule', ast.body)
            self.context.pop_scope(ast.name)
            return (success, result)
        elif isinstance(ast, And):
            (success, value_lhs) = self.interpret(ast.lhs)
            if not success:
                return (False, value_lhs)
            (success, value_rhs) = self.interpret(ast.rhs)
            return (success, value_rhs)
        elif isinstance(ast, Or):
            saved_context = self.context.clone()
            saved_scanner_state = self.scanner.get_state()
            self.event('begin_or', ast.lhs, ast.rhs, saved_context, saved_scanner_state)
            (succeeded, result) = self.interpret(ast.lhs)
            if succeeded:
                self.event('succeed_or', result)
                return (True, result)
            else:
                self.event('fail_or', self.context, self.scanner, result)
                self.context = saved_context
                self.scanner.install_state(saved_scanner_state)
                return self.interpret(ast.rhs)
        elif isinstance(ast, Call):
            prodref = ast.prodref
            module = prodref.module
            name = prodref.name
            args = ast.args
            ibuf = ast.ibuf
            prods = self.program.find_productions(prodref)
            if prods is None:
                print repr(prodref)
                sys.exit(0)
                #raise NotImplementedError(repr(prodref))
            self.event('call_candidates', prods)
            args = [self.interpret(x)[1] for x in args]
            args = [x.expand(self.context) for x in args]
            for prod in prods:
                formals = prod.formals
                self.event('call_args', formals, args)
                if isinstance(formals, list):
                    bindings = Term.match_all(formals, args)
                    self.event('call_bindings', bindings)
                    if bindings != False:
                        if ibuf is not None:
                            return self.interpret_on_buffer(
                                prod, unicode(ibuf.expand(self.context)),
                                bindings=bindings
                            )
                        else:
                            return self.interpret(prod, bindings=bindings)
                else:
                    self.event('call_newfangled_parsing_args', prod)
                    # start a new scope.  arg bindings will appear here.
                    self.context.push_scope(prod.name)
                    (success, result) = self.interpret_on_buffer(
                        formals, unicode(args[0])
                    )
                    # we do not want to start a new scope here, and we
                    # interpret the rule directly, not the prod.
                    if success:
                        self.event('begin_interpret_rule', prod.body)
                        (success, result) = self.interpret(prod.body)
                        self.event('end_interpret_rule', prod.body)
                        self.context.pop_scope(prod.name)
                        return (success, result)
                    else:
                        self.context.pop_scope(prod.name)
            raise ValueError("No '%s' production matched arguments %r" %
                (name, args)
            )
        elif isinstance(ast, Send):
            (success, result) = self.interpret(ast.rule)
            self.context.store(ast.variable.name, result)
            return (success, result)
        elif isinstance(ast, Using):
            sub = ast.rule
            prodref = ast.prodref
            scanner_name = prodref.name
            if prodref.module == '$' and scanner_name == u'byte':
                new_engine = ByteScannerEngine()
            elif prodref.module == '$' and scanner_name == u'utf8':
                new_engine = UTF8ScannerEngine()
            else:
                prods = self.program.find_productions(prodref)
                if len(prods) != 1:
                    raise ValueError("No such scanner '%s'" % scanner_name)
                new_engine = ProductionScannerEngine(self, prods[0])
            self.scanner.push_engine(new_engine)
            self.event('enter_with')
            (succeeded, result) = self.interpret(sub)
            self.event('leave_with', succeeded, result)
            self.scanner.pop_engine()
            return (succeeded, result)
        elif isinstance(ast, Set):
            (success, term) = self.interpret(ast.texpr)
            result = term.expand(self.context)
            self.context.store(ast.variable.name, result)
            return (True, result)
        elif isinstance(ast, Not):
            expr = ast.rule
            saved_context = self.context.clone()
            saved_scanner_state = self.scanner.get_state()
            self.event('begin_not', expr, saved_context, saved_scanner_state)
            (succeeded, result) = self.interpret(expr)
            self.context = saved_context
            self.scanner.install_state(saved_scanner_state)
            if succeeded:
                return (False,
                   Atom("expected anything except '%s', found '%s'" %
                        (repr(expr), self.scanner.peek()))
                )
            else:
                return (True, Atom('nil'))
        elif isinstance(ast, While):
            result = Atom('nil')
            self.event('begin_while')
            succeeded = True
            successful_result = result
            while succeeded:
                saved_context = self.context.clone()
                saved_scanner_state = self.scanner.get_state()
                (succeeded, result) = self.interpret(ast.rule)
                if succeeded:
                    successful_result = result
                    self.event('repeating_while', result)
            self.context = saved_context
            self.scanner.install_state(saved_scanner_state)
            self.event('end_while', result)
            return (True, successful_result)
        elif isinstance(ast, Concat):
            (success, lhs) = self.interpret(ast.lhs)
            lhs = str(lhs.expand(self.context))
            (success, rhs) = self.interpret(ast.rhs)
            rhs = str(rhs.expand(self.context))
            return (True, Atom(lhs + rhs))
        elif isinstance(ast, Term):
            return (True, ast)
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
