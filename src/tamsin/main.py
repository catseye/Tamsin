# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import codecs
import os
import subprocess
import sys

from tamsin.event import DebugEventListener
from tamsin.scanner import EOF, Scanner, UTF8ScannerEngine, TamsinScannerEngine
from tamsin.parser import Parser
from tamsin.interpreter import Interpreter
from tamsin.analyzer import Analyzer
from tamsin.compiler import Compiler


def parse_and_check(filename, scanner_engine=None):
    with open(filename, 'r') as f:
        contents = f.read()
        parser = Parser(contents, scanner_engine=scanner_engine)
        ast = parser.grammar()
        analyzer = Analyzer(ast)
        ast = analyzer.analyze(ast)
        return ast


def run(ast, listeners=None):
    scanner = Scanner(sys.stdin.read(), listeners=listeners)
    scanner.push_engine(UTF8ScannerEngine())
    interpreter = Interpreter(
        ast, scanner, listeners=listeners
    )
    (succeeded, result) = interpreter.interpret_program(ast)
    if not succeeded:
        sys.stderr.write(str(result) + "\n")
        sys.exit(1)
    print str(result)


def main(args, tamsin_dir='.'):
    listeners = []
    if args[0] == '--debug':
        listeners.append(DebugEventListener())
        args = args[1:]
    if args[0] == 'scan':
        scanner = Scanner(sys.stdin.read(), listeners=listeners)
        scanner.push_engine(TamsinScannerEngine())
        tok = None
        while tok is not EOF:
            tok = scanner.consume_any()
            if tok is not EOF:
                print tok
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
        compiler = Compiler(ast, sys.stdout, encoding='UTF-8')
        compiler.compile()
    elif args[0] == 'loadngo':
        ast = parse_and_check(args[1])
        c_filename = 'foo.c'
        exe_filename = './foo'
        with codecs.open(c_filename, 'w', 'UTF-8') as f:
            compiler = Compiler(ast, f)
            compiler.compile()
            c_src_dir = os.path.join(tamsin_dir, 'c_src')
            command = ("gcc", "-g", "-I%s" % c_src_dir, "-L%s" % c_src_dir,
                       c_filename, "-o", exe_filename, "-ltamsin")
            subprocess.check_call(command)
            try:
                subprocess.check_call((exe_filename,))
                exit_code = 0
            except subprocess.CalledProcessError:
                exit_code = 1
            subprocess.call(('rm', '-f', c_filename, exe_filename))
            sys.exit(exit_code)
    else:
        ast = parse_and_check(args[0])
        run(ast, listeners=listeners)
