# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import codecs
import sys

from tamsin.event import DebugEventListener
from tamsin.scanner import EOF, Scanner, CharScannerEngine, TamsinScannerEngine
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
    scanner = Scanner(sys.stdin.read().decode('UTF-8'), listeners=listeners)
    scanner.push_engine(CharScannerEngine())
    interpreter = Interpreter(
        ast, scanner, listeners=listeners
    )
    return interpreter


def run(ast, listeners=None):
    interpreter = mk_interpreter(ast, listeners=listeners)
    (succeeded, result) = interpreter.interpret_program(ast)
    if not succeeded:
        sys.stderr.write(unicode(result).encode('UTF-8') + "\n")
        sys.exit(1)
    print unicode(result)


def main(args):
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
    if args[0] == 'scan':
        scanner = Scanner(sys.stdin.read().decode('UTF-8'), listeners=listeners)
        scanner.push_engine(TamsinScannerEngine())
        tok = None
        while tok is not EOF:
            tok = scanner.consume_any()
            if tok is not EOF:
                print tok.encode('UTF-8')
        print
    elif args[0] == 'parse':
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
        print unicode(ast).encode('UTF-8')
    elif args[0] == 'compile':
        ast = parse_and_check(args[1])
        #print >>sys.stderr, repr(ast)
        compiler = Compiler(ast, sys.stdout)
        compiler.compile()
    else:
        ast = parse_and_check(args[0])
        run(ast, listeners=listeners)
