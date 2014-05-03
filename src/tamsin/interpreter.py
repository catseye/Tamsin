# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

from tamsin.ast import Production
from tamsin.term import Term, Variable
from tamsin.event import EventProducer
from tamsin.scanner import (
    EOF,
    TamsinScannerEngine, CharScannerEngine, ProductionScannerEngine
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
        self.prodmap = program.prodmap

    def __repr__(self):
        return "Interpreter(%r, %r, %r)" % (
            self.program, self.scanner, self.context
        )

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

    def interpret_program(self, program):
        prods = program.find_productions(('PRODREF', '', 'main'))
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
                token = unicode(term)
                if self.scanner.consume(token):
                    return (True, term)
                else:
                    self.event('fail_term', ast.name, self.scanner)
                    s = ("expected '%s' found '%s' (at '%s')" %
                         (token, upcoming_token,
                          self.scanner.report_buffer(self.scanner.position, 20)))
                    return (False, Term(s))
            elif name == '$.return':
                return (True, bindings['X'])
            elif name == '$.eof':
                if self.scanner.eof():
                    return (True, EOF)
                else:
                    return (False, Term("expected EOF found '%s'" %
                            self.scanner.peek()))
            elif name == '$.any':
                if self.scanner.eof():
                    return (False, Term("expected any token, found EOF"))
                else:
                    token = self.scanner.consume_any()
                    return (True, token)
            elif name == '$.alnum':
                if not self.scanner.eof() and self.scanner.peek()[0].isalnum():
                    return (True, self.scanner.consume_any())
                else:
                    return (False, Term("expected alphanumeric, found '%s'" %
                                        self.scanner.peek()))
            elif name == '$.print':
                val = bindings['X']
                print val
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
            (succeeded, x) = self.interpret(ast.body)
            self.event('end_interpret_rule', ast.body)
            self.context.pop_scope(ast.name)
            return (succeeded, x)
        elif ast[0] == 'CALL':
            prodref = ast[1]
            #prodmod = prodref[1]
            name = prodref[2]
            args = ast[2]
            ibuf = ast[3]
            prods = self.program.find_productions(prodref)
            self.event('call_candidates', prods)
            args = [x.expand(self.context) for x in args]
            for prod in prods:
                formals = prod.formals
                self.event('call_args', formals, args)
                if isinstance(formals, list):
                    bindings = self.match_all(formals, args)
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
        elif ast[0] == 'NOT':
            expr = ast[1]
            saved_context = self.context.clone()
            saved_scanner_state = self.scanner.get_state()
            self.event('begin_not', expr, saved_context, saved_scanner_state)
            (succeeded, result) = self.interpret(expr)
            self.context = saved_context
            self.scanner.install_state(saved_scanner_state)
            if succeeded:
                return (False,
                   Term("expected anything except '%s', found '%s'" %
                        (repr(expr), self.scanner.peek()))
                )
            else:
                return (True, Term("nil"))
        elif ast[0] == 'USING':
            sub = ast[1]
            prodref = ast[2]
            scanner_name = prodref[2]
            if scanner_name == u'tamsin':
                new_engine = TamsinScannerEngine()
            elif scanner_name == u'char':
                new_engine = CharScannerEngine()
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
