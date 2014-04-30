#!/usr/bin/env python
# encoding: UTF-8

# Copyright (c)2014 Chris Pressey, Cat's Eye Technologies.
# Distributed under a BSD-style license; see LICENSE for more information.


class EventProducer(object):
    def event(self, tag, *data):
        if self.listeners is None:
            self.listeners = []
        for listener in self.listeners:
            listener.announce(tag, *data)

    def subscribe(self, listener):
        if self.listeners is None:
            self.listeners = []
        self.listeners.append(listener)


class DebugEventListener(object):
    def __init__(self):
        self.indent = 0

    def listen_to(self, producer):
        producer.subscribe(self)

    def putstr(self, s):
        print (self.indent * '  ' + s)
        sys.stdout.flush()

    def announce(self, tag, *data):
        if tag == 'enter_interpreter':
            self.indent += 1
        if tag == 'leave_interpreter':
            self.indent -= 1

        if tag in ('leave_interpreter', 'update_scanner'):
            new_scanner = data[0]
            old_scanner = data[1]
            if (isinstance(new_scanner, CharScanner) and
                isinstance(old_scanner, ProductionScanner)):
                self.putstr("%s %r" % (tag, data))
                new_scanner.dump(self.indent)
                old_scanner.dump(self.indent)
                self.putstr("")
        else:
            pass

        # EVERYTHING
        self.putstr("%s %r" % (tag, data))
        for d in data:
            if getattr(d, 'dump', None) is not None:
                d.dump(self.indent)
        return
         
        if tag in ('enter_interpreter', 'leave_interpreter', 'succeed_or', 'fail_or', 'begin_or'):
            self.putstr("%s %r" % (tag, data))
            return
        elif tag in ('try_literal', 'consume_literal', 'fail_literal'):
            self.putstr("%s %r" % (tag, data))
            data[1].dump(self.indent)
            return
        else:
            return
        ###
        if tag in ('chopped', 'consume', 'scanned'): # ('interpret_ast', 'try_literal'):
            return
        elif tag in ('switched_scanner_forward', 'switched_scanner_back'):
            self.putstr(tag)
            data[0].dump()
            data[1].dump()
        else:
            self.putstr("%s %r" % (tag, data))
