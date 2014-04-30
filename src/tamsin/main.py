#!/usr/bin/env python
# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import codecs
import sys

from tamsin.term import Term, Variable, Concat
from tamsin.event import EventProducer, DebugEventListener
from tamsin.scanner import (
    EOF, enc, Scanner,
    TamsinScannerEngine, CharScannerEngine, ProductionScannerEngine
)
from tamsin.parser import Parser
from tamsin.interpreter import Interpreter



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
            scanner.push_engine(CharScannerEngine())
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
