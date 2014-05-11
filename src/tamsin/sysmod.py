# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.

# Python version of Tamsin's $ module.

import sys

from tamsin.term import EOF, Atom, Constructor


TRANSLATOR = {'return': 'return_', 'print': 'print_'}


def call(name, interpreter, args):
    name = TRANSLATOR.get(name, name)
    if name not in globals():
        raise NotImplementedError(name)
    return globals()[name](interpreter, args)


def arity(name):
    name = TRANSLATOR.get(name, name)
    if name not in globals():
        raise NotImplementedError(name)
    return globals()[name].arity


def return_(self, args):
    return (True, args[0])
return_.arity = 1


def fail(self, args):
    return (False, args[0])
fail.arity = 1


def expect(self, args):
    upcoming_token = self.scanner.peek()
    term = args[0]
    token = str(term)
    if self.scanner.consume(token):
        return (True, term)
    else:
        s = ("expected '%s' found '%s' (at '%s')" %
             (token, upcoming_token,
              self.scanner.report_buffer(self.scanner.position, 20)))
        return (False, Atom(s))
expect.arity = 1


def eof(self, args):
    if self.scanner.peek() is EOF:
        return (True, EOF)
    else:
        return (False, Atom("expected EOF found '%s'" %
                self.scanner.peek()))
eof.arity = 0


def any(self, args):
    if self.scanner.peek() is EOF:
        return (False, Atom("expected any token, found EOF"))
    else:
        return (True, Atom(self.scanner.consume_any()))
any.arity = 0


def alnum(self, args):
    if (self.scanner.peek() is not EOF and
        self.scanner.peek()[0].isalnum()):
        return (True, Atom(self.scanner.consume_any()))
    else:
        return (False, Atom("expected alphanumeric, found '%s'" %
                            self.scanner.peek()))
alnum.arity = 0


def upper(self, args):
    if (self.scanner.peek() is not EOF and
        self.scanner.peek()[0].isupper()):
        return (True, Atom(self.scanner.consume_any()))
    else:
        return (False, Atom("expected uppercase alphabetic, found '%s'" %
                            self.scanner.peek()))
upper.arity = 0


def startswith(self, args):
    if (self.scanner.peek() is not EOF and
        self.scanner.peek()[0].startswith((str(args[0]),))):
        return (True, Atom(self.scanner.consume_any()))
    else:
        return (False, Atom("expected '%s, found '%s'" %
                            (args[0], self.scanner.peek())))
startswith.arity = 1


def equal(self, args):
    if args[0].match(args[1]) != False:
        return (True, args[0])
    else:
        return (False, Atom("term '%s' does not equal '%s'" %
                            (args[0], args[1])))
equal.arity = 2


def unquote(self, args):
    x = str(args[0])
    if (x.startswith((str(args[1]),)) and
        x.endswith((str(args[2]),))):
        return (True, Atom(x[1:-1]))
    else:
        return (False, Atom("term '%s' is not quoted with '%s' and '%s'" %
                            (args[0], args[1], args[2])))
unquote.arity = 3


def mkterm(self, args):
    t = args[0]
    l = args[1]
    contents = []
    while isinstance(l, Constructor) and l.tag == 'list':
        contents.append(l.contents[0])
        l = l.contents[1]
    if contents:
        return (True, Constructor(t.text, contents))
    else:
        return (True, t)
mkterm.arity = 2


def reverse(self, args):
    return (True, args[0].reversed(args[1]))
reverse.arity = 2


def print_(self, args):
    val = args[0]
    sys.stdout.write(str(val))
    sys.stdout.write("\n")
    return (True, val)
print_.arity = 1


def emit(self, args):
    val = args[0]
    sys.stdout.write(str(val))
    return (True, val)
emit.arity = 1


def repr(self, args):
    val = args[0]
    val = Atom(val.repr())
    return (True, val)
repr.arity = 1


counter = 0

def gensym(self, args):
    global counter
    counter += 1
    return (True, Atom(str(args[0]) + str(counter)))
gensym.arity = 1


def hexbyte(self, args):
    return (True, Atom(chr(int(args[0].text + args[1].text, 16))))
hexbyte.arity = 2
