Tamsin Release History
======================

0.3-PRE
-------

### language ###

*   (Partially) defined what it means to `reprify` a term.
*   Clarified some matters as implementation-defined.

### modules ###

*   `$:equal` now does deep equality of arbitrary ground terms.
*   `$:repr` added.
*   `$:reverse` added.

### implementations ###

*   Virtually full support for user-defined modules.  (Not external ones
    yet though.)
*   `tamsin parse` and `tamsin-parser.tamsin` output reprified terms.

0.2
---

### language ###

*   Module-member syntax changed from `.` to `:`.
*   `:` can be used without any module on the LHS to refer to a production
    in the current module.
*   Added "fold" forms, binary `/` and ternary `//`.

### modules ###

*   `$:char` scanner dropped.  Instead, there are `$:byte` (which always
    returns 8-bit-clean bytes) and `$:utf8` (which always returns UTF-8
    sequences.)
*   Added `$:equal(L,R)`.
*   `$:unquote(X,L,R)` takes three arguments now.

### implementations ###

*   Beginnings of user-defined module support (very rudimentary, not to be
    used.)
*   Code in `libtamsin` is much more robust.  AST-builder written in Tamsin now
    compiles and runs correctly.
*   Added a desugaring phase to `tamsin`, and a desugarer written in Tamsin.
*   Added Micro-Tamsin interpreter, written in Tamsin.  Can pass the first
    30 tests from the spec.

0.1
---

Initial release.
