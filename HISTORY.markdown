Tamsin Release History
======================

0.2
---

*   Module-member syntax changed from `.` to `:`.
*   Beginnings of user-defined module support (very rudimentary, not to be
    used.)
*   `:` can be used without any module on the LHS to refer to a production
    in the current module.
*   `$:char` scanner dropped.  Instead, there are `$:byte` (which always
    returns 8-bit-clean bytes) and `$:utf8` (which always returns UTF-8
    sequences.)
*   Added "fold" forms, binary `/` and ternary `//`.
*   Code in `libtamsin` is much more robust.  AST-builder written in Tamsin now
    compiles and runs correctly.
*   Added a desugaring phase to `tamsin`, and a desugarer written in Tamsin.
*   Added `$:equal(L,R)`.
*   `$:unquote(X,L,R)` takes three arguments now.
*   Added Micro-Tamsin interpreter, written in Tamsin.  Can pass the first
    30 tests from the spec.

0.1
---

Initial release.
