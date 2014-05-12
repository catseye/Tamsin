#!/bin/sh -x

cd c_src && ./build.sh && cd ..

exit 0

# not used yet -- should be Makefile

build() {
    SRC=$1
    LIBS=$2
    BIN=$3

    bin/tamsin compile $LIBS $SRC > tmp/foo.c && \
       gcc -g -Ic_src -Lc_src tmp/foo.c -o $BIN -ltamsin || exit 1
}

build "mains/tamsin-grammar.tamsin" \
      "lib/tamsin_scanner.tamsin" \
      "bin/tamsin-grammar"
build "mains/scanner.tamsin" \
      "lib/tamsin_scanner.tamsin" \
      "bin/tamsin-scanner"
build "mains/parser.tamsin" \
      "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin" \
      "bin/tamsin-parser"
build "mains/desugarer.tamsin" \
      "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
      "bin/tamsin-desugarer"
build "mains/analyzer.tamsin" \
      "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
      "bin/tamsin-analyzer"
build "mains/compiler.tamsin" \
      "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
      "bin/tamsin-compiler"
