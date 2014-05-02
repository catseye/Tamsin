# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import codecs
import sys

from tamsin.event import DebugEventListener
from tamsin.scanner import Scanner, CharScannerEngine
from tamsin.parser import Parser
from tamsin.interpreter import Interpreter
from tamsin.analyzer import Analyzer
from tamsin.compiler import Compiler


def parse_and_check(filename):
    with codecs.open(filename, 'r', 'UTF-8') as f:
        contents = f.read()
        parser = Parser(contents)
        ast = parser.grammar()
        analyzer = Analyzer(ast)
        ast = analyzer.analyze(ast)
        return ast


def run(filename, listeners=None):
    ast = parse_and_check(filename)
    scanner = Scanner(sys.stdin.read(), listeners=listeners)
    scanner.push_engine(CharScannerEngine())
    interpreter = Interpreter(
        ast, scanner, listeners=listeners
    )
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
    elif args[0] == 'run':
        run(args[1], listeners=listeners)
    elif args[0] == 'compile':
        ast = parse_and_check(args[1])
        #print >>sys.stderr, repr(ast)
        compiler = Compiler(ast, sys.stdout)
        compiler.compile()
    else:
        run(args[0], listeners=listeners)
    