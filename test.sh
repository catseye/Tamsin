#!/bin/sh

FILES="
    doc/Tamsin.markdown
    doc/Tested_Examples.markdown
"
if [ x$1 = x ]; then
   $0 interpreter &&
   $0 compiler &&
   #$0 scanner &&
   #$0 parser &&
   $0 ast &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xtamsin ]; then
   echo "Testing things written in Tamsin only."
   $0 ast &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xthorough ]; then
   echo "Testing EVERYTHING.  Will likely take more than 5 minutes."
   $0 interpreter &&
   $0 compiler &&
   $0 scanner &&
   $0 parser &&
   $0 ast &&
   $0 desugarer &&
   $0 analyzer &&
   $0 micro &&
   echo "All tests passed!"
   exit $?
fi

if [ x$2 != x -a -e $2 ]; then
    echo "(Testing on file $2 only)"
    FILES=$2
fi

testcompiled() {
    SRC=$1
    LIBS=$2
    CMD=$3
    BIN=$4

    echo "Compiling $1 and testing it against '$2'..."
    ./build.sh
    bin/tamsin compile $LIBS $SRC > foo.c && \
       gcc -g -Ic_src -Lc_src foo.c -o $BIN -ltamsin || exit 1
    for EG in eg/*.tamsin; do
        echo $EG
        $CMD $EG > 1.txt
        ./$BIN <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
}

if [ x$1 = xcompiler ]; then
    echo "Testing compiler..."
    ./build.sh || exit 1
    falderal $VERBOSE --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xscanner ]; then
    echo "Testing scanner in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin scan <$EG > 1.txt || exit 1
        bin/tamsin lib/tamsin_scanner.tamsin \
                   mains/scanner.tamsin <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xgrammar ]; then
    echo "Testing parser (for syntactic correctness only) in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin lib/tamsin_scanner.tamsin \
                   mains/tamsin-grammar.tamsin <$EG || exit 1
    done
elif [ x$1 = xinterpretedast ]; then
    echo "Testing parser (for AST) in Tamsin..."
    for EG in eg/*.tamsin; do
        echo $EG
        bin/tamsin parse $EG > 1.txt
        bin/tamsin lib/tamsin_scanner.tamsin \
                   lib/tamsin_parser.tamsin \
                   mains/parser.tamsin <$EG > 2.txt || exit 1
        diff -ru 1.txt 2.txt > ast.diff
        diff -ru 1.txt 2.txt || exit 1
    done
elif [ x$1 = xast ]; then   # check that tamsin-ast output looks like bin/tamsin parse
    testcompiled "mains/parser.tamsin" \
                 "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin" \
                 "./bin/tamsin parse" \
                 "tamsin-ast"
elif [ x$1 = xdesugarer ]; then
    testcompiled "mains/desugarer.tamsin" \
                 "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                 "./bin/tamsin desugar" \
                 "tamsin-desugarer"
elif [ x$1 = xanalyzer ]; then
    testcompiled "mains/analyzer.tamsin" \
                 "lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                 "./bin/tamsin analyze" \
                 "tamsin-analyzer"
elif [ x$1 = xmicro ]; then
    echo "Compiling Micro-Tamsin interpreter..."
    ./build.sh
    bin/tamsin compile lib/tamsin_scanner.tamsin \
                       lib/tamsin_parser.tamsin \
                       mains/micro-tamsin.tamsin > foo.c && \
       gcc -g -ansi -Werror \
           -Ic_src -Lc_src foo.c -o micro-tamsin -ltamsin || exit 1
    echo "Testing Micro-Tamsin interpreter..."
    FILES="doc/Micro-Tamsin.markdown"
    falderal $VERBOSE --substring-error fixture/micro-tamsin.markdown $FILES
elif [ x$1 = xinterpreter -o x$1 = xi ]; then
    echo "Testing Python interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $FILES
fi
