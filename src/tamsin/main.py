# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import codecs
import sys

from tamsin.event import DebugEventListener
from tamsin.scanner import Scanner, CharScannerEngine, ProductionScannerEngine
from tamsin.parser import Parser
from tamsin.interpreter import Interpreter
from tamsin.analyzer import Analyzer
from tamsin.compiler import Compiler


def parse_and_check(filename, scanner_engine=None):
    with codecs.open(filename, 'r', 'UTF-8') as f:
        contents = f.read()
        parser = Parser(contents, scanner_engine=scanner_engine)
        ast = parser.grammar()
        analyzer = Analyzer(ast)
        ast = analyzer.analyze(ast)
        return ast


def mk_interpreter(ast, listeners=None):
    scanner = Scanner(sys.stdin.read(), listeners=listeners)
    scanner.push_engine(CharScannerEngine())
    interpreter = Interpreter(
        ast, scanner, listeners=listeners
    )
    return interpreter


def run(ast, listeners=None):
    interpreter = mk_interpreter(ast, listeners=listeners)
    (succeeded, result) = interpreter.interpret_program(ast)
    if not succeeded:
        sys.stderr.write(str(result) + "\n")
        sys.exit(1)
    print str(result)


def main(args):
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
    if args[0] == 'parse':
        ast = parse_and_check(args[1])
        print repr(ast)
    elif args[0] == 'runscan':
        tamsin_scanner_ast = parse_and_check('eg/tamsin-scanner.tamsin')
        print repr(tamsin_scanner_ast)
        scanner_interpreter = mk_interpreter(tamsin_scanner_ast)
        s = ProductionScannerEngine(scanner_interpreter,
            tamsin_scanner_ast.find_productions(
                ('PRODREF', '', 'tamsin')
            )[0])
        ast = parse_and_check(args[1], scanner_engine=s)
        run(ast, listeners=listeners)
    elif args[0] == 'compile':
        ast = parse_and_check(args[1])
        #print >>sys.stderr, repr(ast)
        compiler = Compiler(ast, sys.stdout)
        compiler.compile()
    else:
        ast = parse_and_check(args[0])
        run(ast, listeners=listeners)
    