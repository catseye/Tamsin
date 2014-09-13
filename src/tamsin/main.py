# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

import os
import subprocess
import sys

from tamsin.buffer import FileBuffer
from tamsin.event import DebugEventListener
from tamsin.term import Atom
from tamsin.scanner import (
    Scanner, EOF, UTF8ScannerEngine, TamsinScannerEngine
)
from tamsin.parser import Parser
from tamsin.interpreter import Interpreter
from tamsin.desugarer import Desugarer
from tamsin.analyzer import Analyzer
from tamsin.compiler import Compiler


def parse(filename):
    with open(filename, 'r') as f:
        scanner = Scanner(
            FileBuffer(f, filename=filename),
            engines=(TamsinScannerEngine(),)
        )
        parser = Parser(scanner)
        ast = parser.grammar()
        desugarer = Desugarer(ast)
        ast = desugarer.desugar(ast)
        return ast


def parse_and_check_args(args):
    ast = None
    for arg in args:
        next_ast = parse(arg)
        if ast is None:
            ast = next_ast
        else:
            ast.incorporate(next_ast)
    analyzer = Analyzer(ast)
    ast = analyzer.analyze(ast)
    return ast


def run(ast, listeners=None):
    scanner = Scanner(
        FileBuffer(sys.stdin, filename='<stdin>'),
        engines=(UTF8ScannerEngine(),),
        listeners=listeners
    )
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
        with open(args[1], 'r') as f:
            scanner = Scanner(
                FileBuffer(f, filename=args[1]),
                engines=(TamsinScannerEngine(),),
                listeners=listeners
            )
        tok = None
        while tok is not EOF:
            tok = scanner.scan()
            if tok is not EOF:
                print Atom(tok).repr()
        print
    elif args[0] == 'parse':
        parser = Parser.for_file(args[1])
        ast = parser.grammar()
        print str(ast)
    elif args[0] == 'desugar':
        parser = Parser.for_file(args[1])
        ast = parser.grammar()
        desugarer = Desugarer(ast)
        ast = desugarer.desugar(ast)
        print str(ast)
    elif args[0] == 'analyze':
        ast = parse_and_check_args(args[1:])
        print str(ast)
    elif args[0] == 'compile':
        ast = parse_and_check_args(args[1:])
        compiler = Compiler(ast, sys.stdout)
        compiler.compile()
    elif args[0] == 'doublecompile':
        # http://www.youtube.com/watch?v=6WxJECOFg8w
        ast = parse_and_check_args(args[1:])
        c_filename = 'foo.c'
        exe_filename = './foo'
        with open(c_filename, 'w') as f:
            compiler = Compiler(ast, f)
            compiler.compile()
        c_src_dir = os.path.join(tamsin_dir, 'c_src')
        command = ("gcc", "-g", "-I%s" % c_src_dir, "-L%s" % c_src_dir,
                   c_filename, "-o", exe_filename, "-ltamsin")
        try:
            subprocess.check_call(command)
            exit_code = 0
        except subprocess.CalledProcessError:
            exit_code = 1
        #subprocess.call(('rm', '-f', c_filename))
        sys.exit(exit_code)
    elif args[0] == 'loadngo':
        ast = parse_and_check_args(args[1:])
        c_filename = 'foo.c'
        exe_filename = './foo'
        with open(c_filename, 'w') as f:
            compiler = Compiler(ast, f)
            compiler.compile()
        c_src_dir = os.path.join(tamsin_dir, 'c_src')
        command = ("gcc", "-g", "-I%s" % c_src_dir, "-L%s" % c_src_dir,
                   c_filename, "-o", exe_filename, "-ltamsin")
        try:
            subprocess.check_call(command)
            subprocess.check_call((exe_filename,))
            exit_code = 0
        except subprocess.CalledProcessError:
            exit_code = 1
        subprocess.call(('rm', '-f', c_filename, exe_filename))
        sys.exit(exit_code)
    else:
        ast = parse_and_check_args(args)
        run(ast, listeners=listeners)
