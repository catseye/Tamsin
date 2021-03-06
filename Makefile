CC?=gcc
CFLAGS?=-ansi -g -Ic_src -Lc_src

LCFLAGS?=-ansi -pedantic -g -Wall -Werror -Ic_src -Lc_src

##### libtamsin #####

OBJECTS=c_src/dict.o c_src/scanner.o c_src/term.o c_src/tamsin.o
PROGS=bin/tamsin-compiler bin/micro-tamsin

all: c_src/libtamsin.a

c_src/scanner.o: c_src/tamsin.h c_src/scanner.c
	$(CC) $(LCFLAGS) -c c_src/scanner.c -o $@

c_src/term.o: c_src/tamsin.h c_src/term.c
	$(CC) $(LCFLAGS) -c c_src/term.c -o $@

c_src/tamsin.o: c_src/tamsin.h c_src/tamsin.c
	$(CC) $(LCFLAGS) -c c_src/tamsin.c -o $@

c_src/libtamsin.a: $(OBJECTS)
	ar -r $@ $(OBJECTS)


##### executables #####

TAMSIN_COMPILER_LIBS=lib/list.tamsin lib/tamsin_scanner.tamsin \
                     lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin
bin/tamsin-compiler: c_src/libtamsin.a c_src/tamsin.h \
                     $(TAMSIN_COMPILER_LIBS) \
                     mains/compiler.tamsin
	bin/tamsin compile $(TAMSIN_COMPILER_LIBS) mains/compiler.tamsin > tmp/foo.c
	$(CC) $(CFLAGS) tmp/foo.c -o $@ -ltamsin


bin/bootstrapped-compiler: c_src/libtamsin.a c_src/tamsin.h \
                           bin/tamsin-compiler \
                           $(TAMSIN_COMPILER_LIBS) \
                          mains/compiler.tamsin
	bin/tamsin-compiler $(TAMSIN_COMPILER_LIBS) mains/compiler.tamsin > tmp/foo.c
	$(CC) $(CFLAGS) tmp/foo.c -o $@ -ltamsin


MICRO_TAMSIN_LIBS=lib/list.tamsin lib/tamsin_scanner.tamsin \
                  lib/tamsin_parser.tamsin
bin/micro-tamsin: c_src/libtamsin.a c_src/tamsin.h \
                     $(MICRO_TAMSIN_LIBS) \
                     mains/micro-tamsin.tamsin
	bin/tamsin compile $(MICRO_TAMSIN_LIBS) mains/micro-tamsin.tamsin > tmp/foo.c
	$(CC) $(CFLAGS) tmp/foo.c -o $@ -ltamsin


MINI_TAMSIN_LIBS=lib/list.tamsin lib/tamsin_scanner.tamsin \
                 lib/tamsin_parser.tamsin
bin/mini-tamsin: c_src/libtamsin.a c_src/tamsin.h \
                     $(MINI_TAMSIN_LIBS) \
                     mains/mini-tamsin.tamsin
	bin/tamsin compile $(MINI_TAMSIN_LIBS) mains/mini-tamsin.tamsin > tmp/foo.c
	$(CC) $(CFLAGS) tmp/foo.c -o $@ -ltamsin

clean:
	rm -f c_src/libtamsin.a c_src/*.o $(PROGS)
