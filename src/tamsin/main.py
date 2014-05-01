#!/usr/bin/env python
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
        analyzer.analyze(ast)
        return analyzer


def main(args):
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
    if args[0] == 'parse':
        a = parse_and_check(args[1])
        print repr(a.program)
    elif args[0] == 'run':
        a = parse_and_check(args[1])
        scanner = Scanner(sys.stdin.read(), listeners=listeners)
        scanner.push_engine(CharScannerEngine())
        interpreter = Interpreter(
            a.program, scanner, a.prodmap, listeners=listeners
        )
        (succeeded, result) = interpreter.interpret(a.program)
        if not succeeded:
            sys.stderr.write(str(result) + "\n")
            sys.exit(1)
        print str(result)
    elif args[0] == 'compile':
        a = parse_and_check(args[1])
        compiler = Compiler(sys.stdout, a.prodmap, a.localsmap)
        compiler.compile(a.program)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")
