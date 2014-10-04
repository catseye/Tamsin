#!/bin/sh

for FILE in eg/hello-world.tamsin eg/bits.tamsin eg/bitpair.tamsin; do
  tamsin codegen $FILE || exit 1
done
