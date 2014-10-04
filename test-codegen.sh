#!/bin/sh

FILES="
eg/hello-world.tamsin eg/bits.tamsin eg/bitpair.tamsin
eg/exciting-long.tamsin
"

for FILE in $FILES; do
  tamsin codegen $FILE || exit 1
done
