#!/bin/sh -x

FILES="scanner term tamsin"

for FILE in $FILES; do
    gcc -ansi -pedantic -g -Wall -Werror -c $FILE.c -o $FILE.o || exit 1
done

ar -r libtamsin.a scanner.o term.o tamsin.o

