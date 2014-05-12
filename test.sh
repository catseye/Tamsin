#!/bin/sh

FILES="
    doc/Tamsin.markdown
    doc/Tested_Examples.markdown
"
GLOB="eg/*.tamsin lib/*.tamsin mains/*.tamsin"

mkdir -p tmp
make all || exit 1

if [ x$1 = 'x-f' ]; then
    shift
    echo "(Testing on Falderal files '$1' only)"
    FILES=$1
    shift
fi

MODE=compiled
if [ x$1 = xcompiled -o x$1 = xinterpreted ]; then
    MODE=$1
    shift
fi

if [ x$1 = x ]; then
   $0 interpreter &&
   $0 compiler &&
   $0 tcompiler &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xtamsin ]; then
   echo "Testing things written in Tamsin only."
   $0 compiled scanner &&
   $0 compiled grammar &&
   $0 compiled parser &&
   $0 compiled desugarer &&
   $0 compiled analyzer &&
   $0 micro &&
   $0 tcompiler &&
   echo "All tests passed!"
   exit $?
fi

if [ x$1 = xthorough ]; then
   echo "Testing EVERYTHING.  Will likely take more than 5 minutes."
   $0 interpreter &&
   $0 compiler &&
   $0 interpreted scanner &&
   $0 interpreted grammar &&
   $0 interpreted parser &&
   $0 interpreted desugarer &&
   $0 interpreted analyzer &&
   $0 compiled scanner &&
   $0 compiled grammar &&
   $0 compiled parser &&
   $0 compiled desugarer &&
   $0 compiled analyzer &&
   $0 micro &&
   $0 tcompiler &&
   $0 bootstrap &&
   echo "All tests passed!"
   exit $?
fi

ok() {
    echo 'ok'
}

test_it() {
    MODE=$1
    SRC=$2
    LIBS=$3
    CMD=$4
    BIN=$5
    if [ x$BIN = x ]; then
        BIN=foo
    fi

    if [ $MODE = "compiled" ]; then
        echo "*** Compiling $SRC (with $LIBS)"
        echo "*** and testing it against '$CMD'..."
        bin/tamsin compile $LIBS $SRC > tmp/foo.c && \
           gcc -g -Ic_src -Lc_src tmp/foo.c -o $BIN -ltamsin || exit 1
        for EG in $GLOB; do
            echo $EG
            $CMD $EG | bin/wrap > tmp/python-cmd.txt
            $BIN <$EG | bin/wrap > tmp/tamsin-cmd.txt
            diff -ru tmp/python-cmd.txt tmp/tamsin-cmd.txt > tmp/output.diff
            diff -ru tmp/python-cmd.txt tmp/tamsin-cmd.txt || exit 1
        done
    elif [ $MODE = "interpreted" ]; then
        echo "*** Interpreting $SRC (with $LIBS)"
        echo "*** and testing it against '$CMD'..."
        for EG in $GLOB; do
            echo $EG
            $CMD $EG | bin/wrap > tmp/python-cmd.txt
            bin/tamsin $LIBS $SRC <$EG | bin/wrap > tmp/tamsin-cmd.txt
            diff -ru tmp/python-cmd.txt tmp/tamsin-cmd.txt > tmp/output.diff
            diff -ru tmp/python-cmd.txt tmp/tamsin-cmd.txt || exit 1
        done
        echo "Passed."
        exit 0
    else
        echo "BAD MODE"
        exit 1
    fi
    echo "Passed."
    exit 0
}

if [ x$1 = xcompiler ]; then
    echo "*** Testing compiler..."
    falderal $VERBOSE --substring-error fixture/compiler.py.markdown $FILES
elif [ x$1 = xinterpreter -o x$1 = xi ]; then
    echo "*** Testing Python interpreter..."
    falderal $VERBOSE --substring-error fixture/tamsin.py.markdown $FILES
elif [ x$1 = xgrammar ]; then
    test_it $MODE "mains/grammar.tamsin" \
                  "lib/tamsin_scanner.tamsin" \
                  "ok" \
                  "bin/tamsin-grammar"
elif [ x$1 = xscanner ]; then
    test_it $MODE "mains/scanner.tamsin" \
                  "lib/tamsin_scanner.tamsin" \
                  "./bin/tamsin scan" \
                  "bin/tamsin-scanner"
elif [ x$1 = xparser ]; then
    test_it $MODE "mains/parser.tamsin" \
                  "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin" \
                  "./bin/tamsin parse" \
                  "bin/tamsin-parser"
elif [ x$1 = xdesugarer ]; then
    test_it $MODE "mains/desugarer.tamsin" \
                  "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                  "./bin/tamsin desugar" \
                  "bin/tamsin-desugarer"
elif [ x$1 = xanalyzer ]; then
    # libs and mains need libs
    GLOB="eg/*.tamsin"
    test_it $MODE "mains/analyzer.tamsin" \
                  "lib/list.tamsin lib/tamsin_scanner.tamsin lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin" \
                  "./bin/tamsin analyze" \
                  "bin/tamsin-analyzer"
elif [ x$1 = xtcompiler ]; then
    echo "*** Testing Tamsin-in-Tamsin compiler..."
    falderal $VERBOSE --substring-error fixture/compiler.tamsin.markdown $FILES
elif [ x$1 = xbootstrap ]; then
    echo "*** Compiling Bootstrapped Tamsin-in-Tamsin compiler..."
    bin/tamsin-compiler lib/list.tamsin lib/tamsin_scanner.tamsin \
                        lib/tamsin_parser.tamsin lib/tamsin_analyzer.tamsin \
                        mains/compiler.tamsin > tmp/foo.c && \
       gcc -g -ansi -Werror \
           -Ic_src -Lc_src tmp/foo.c -o bin/bootstrapped-compiler -ltamsin || exit 1
    echo "*** Testing Bootstrapped Tamsin-in-Tamsin compiler..."
    falderal $VERBOSE --substring-error fixture/bootstrapped.markdown $FILES
elif [ x$1 = xmicro ]; then
    echo "*** Testing Micro-Tamsin interpreter..."
    FILES="doc/Micro-Tamsin.markdown"
    falderal $VERBOSE --substring-error fixture/micro-tamsin.markdown $FILES
else
    echo "Unknown test '$1'."
    exit 1
fi
