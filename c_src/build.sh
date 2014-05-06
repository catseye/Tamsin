#!/bin/sh -x

FILES="scanner term tamsin"

for FILE in $FILES; do
    gcc -ansi -pedantic -g -c $FILE.c -o $FILE.o
done

ar -r libtamsin.a scanner.o term.o tamsin.o

