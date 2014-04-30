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


def main(args):
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
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
    elif args[0] == 'compile':
        from tamsin.compiler import compile
        with codecs.open(args[1], 'r', 'UTF-8') as f:
            contents = f.read()
            parser = Parser(contents)
            ast = parser.grammar()
            compile(ast, sys.stdout)
    else:
        raise ValueError("first argument must be 'parse' or 'run'")
