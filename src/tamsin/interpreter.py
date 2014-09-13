# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.


from tamsin.ast import (
    Production, And, Or, Not, While, Call, Send, Set, Using, On,
    Prodref, Concat, TermNode
)
from tamsin.buffer import StringBuffer
from tamsin.term import Term, Atom
from tamsin.event import EventProducer
from tamsin.scanner import (
    ByteScannerEngine, UTF8ScannerEngine, ProductionScannerEngine
)
import tamsin.sysmod


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
        main = program.find_production(Prodref('main', 'main'))
        if not main:
            raise ValueError("no 'main:main' production defined")
        return self.interpret(main)

    def interpret(self, ast, args=None):
        """Returns a pair (bool, result) where bool is True if it
        succeeded and False if it failed.

        """
        self.event('interpret_ast', ast)
        if isinstance(ast, Production):
            name = ast.name
            bindings = False
            branch = None
            for b in ast.branches:
                formals = [self.interpret(f)[1] for f in b.formals]
                self.event('call_args', formals, args)
                if isinstance(formals, list):
                    bindings = Term.match_all(formals, args)
                    self.event('call_bindings', bindings)
                    if bindings != False:
                        branch = b
                        break
                # else:
                #     self.event('call_newfangled_parsing_args', prod)
                #     # start a new scope.  arg bindings will appear here.
                #     self.context.push_scope(prod.name)
                #     (success, result) = self.interpret_on_buffer(
                #         formals, unicode(args[0])
                #     )
                #     # we do not want to start a new scope here, and we
                #     # interpret the rule directly, not the prod.
                #     if success:
                #         self.event('begin_interpret_rule', prod.body)
                #         (success, result) = self.interpret(prod.body)
                #         self.event('end_interpret_rule', prod.body)
                #         self.context.pop_scope(prod.name)
                #         return (success, result)
                #     else:
                #         self.context.pop_scope(prod.name)
            if branch is None:
                raise ValueError("No '%s' production matched arguments %r" %
                    (name, args)
                )

            self.context.push_scope(name)
            if bindings != False:
                for name in bindings.keys():
                    self.context.store(name, bindings[name])
            self.event('begin_interpret_rule', branch.body)
            assert branch.body, repr(ast)
            (success, result) = self.interpret(branch.body)
            self.event('end_interpret_rule', branch.body)
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
            self.scanner.save_state()
            self.event('begin_or', ast.lhs, ast.rhs, saved_context)
            (succeeded, result) = self.interpret(ast.lhs)
            if succeeded:
                self.event('succeed_or', result)
                self.scanner.pop_state()
                return (True, result)
            else:
                self.event('fail_or', self.context, self.scanner, result)
                self.context = saved_context
                self.scanner.restore_state("after or")
                return self.interpret(ast.rhs)
        elif isinstance(ast, Call):
            prodref = ast.prodref
            name = prodref.name
            args = [self.interpret(x)[1] for x in ast.args]
            args = [x.expand(self.context) for x in args]
            for a in args:
                assert isinstance(a, Term)
            if prodref.module == '$':
                return tamsin.sysmod.call(name, self, args)
            prod = self.program.find_production(prodref)
            assert prod is not None, "unresolved: " + repr(prodref)
            self.event('call_candidates', prod)
            return self.interpret(prod, args=args)
        elif isinstance(ast, Send):
            (success, result) = self.interpret(ast.rule)
            #(success, variable) = self.interpret(ast.pattern)  # ... ?
            #self.context.store(variable.name, result)
            formals = [self.interpret(f)[1] for f in [ast.pattern]]
            bindings = Term.match_all(formals, [result])
            if bindings == False:
                return (False, Atom('nomatch'))
            for name in bindings.keys():
                self.context.store(name, bindings[name])
            return (success, result)
        elif isinstance(ast, Using):
            sub = ast.rule
            prodref = ast.prodref
            scanner_name = prodref.name
            if prodref.module == '$' and scanner_name == 'byte':
                new_engine = ByteScannerEngine()
            elif prodref.module == '$' and scanner_name == 'utf8':
                new_engine = UTF8ScannerEngine()
            else:
                prod = self.program.find_production(prodref)
                if not prod:
                    raise ValueError("No such scanner '%s'" % scanner_name)
                new_engine = ProductionScannerEngine(self, prod)
            self.scanner.push_engine(new_engine)
            self.event('enter_with')
            (succeeded, result) = self.interpret(sub)
            self.event('leave_with', succeeded, result)
            self.scanner.pop_engine()
            return (succeeded, result)
        elif isinstance(ast, On):
            (success, result) = self.interpret(ast.texpr)
            buffer = str(result.expand(self.context))
            self.event('interpret_on_buffer', buffer)
            previous_buffer = self.scanner.get_buffer()
            self.scanner.install_buffer(StringBuffer(buffer))
            (success, result) = self.interpret(ast.rule)
            self.scanner.install_buffer(previous_buffer)
            return (success, result)
        elif isinstance(ast, Set):
            (success, variable) = self.interpret(ast.variable)
            (success, term) = self.interpret(ast.texpr)
            result = term.expand(self.context)
            self.context.store(variable.name, result)
            return (True, result)
        elif isinstance(ast, Not):
            expr = ast.rule
            saved_context = self.context.clone()
            self.scanner.save_state()
            self.event('begin_not', expr, saved_context)
            (succeeded, result) = self.interpret(expr)
            self.context = saved_context
            self.scanner.restore_state("after not")
            if succeeded:
                return (False, Atom(self.scanner.error_message(
                    "anything else", self.scanner.peek()
                )))
            else:
                return (True, Atom('nil'))
        elif isinstance(ast, While):
            result = Atom('nil')
            self.event('begin_while')
            succeeded = True
            successful_result = result
            while succeeded:
                saved_context = self.context.clone()
                self.scanner.save_state()
                (succeeded, result) = self.interpret(ast.rule)
                if succeeded:
                    self.scanner.pop_state()
                    successful_result = result
                    self.event('repeating_while', result)
                else:
                    self.scanner.restore_state("after while")
            self.context = saved_context
            self.event('end_while', result)
            return (True, successful_result)
        elif isinstance(ast, Concat):
            (success, lhs) = self.interpret(ast.lhs)
            lhs = str(lhs.expand(self.context))
            (success, rhs) = self.interpret(ast.rhs)
            rhs = str(rhs.expand(self.context))
            return (True, Atom(lhs + rhs))
        elif isinstance(ast, TermNode):
            return (True, ast.to_term())
        else:
            raise NotImplementedError(repr(ast))
