TODO
----

*   figure out why compiled version of tamsin-ast hangs...
*   definitely there's some kind of a problem with alnum vs eof in our C code

### 8-bit clean/UTF-8 ###

*   arbitrary non-printable characters in terms: `\x99`
*   `byte` versus `utf_8` scanners ("char" is vague, isn't it?)
*   `byte` scanner must be 8-bit clean, i.e. can return `\x00`
*   `emit` alongside `print`.
*   `emit` must be 8-bit clean, i.e. can emit `\x00`
*   `utf_8` scanner must yield a Unicode char when it finds one encoded in UTF-8
*   tests for all these
*   implement all these in both Python and C

### lower-priority/experimental ###

*   tell/rewind the implicit buffer -- for VM's etc
*   `using` production x: x's scanner defaults to byte or utf_8, not x
*   figure out good way to do aliases with the Tamsin-parser-in-Tamsin
    (dynamic grammar is really more of a Zz thing...)
*   productions with names with arbitrary characters in them.
*   something like «foo» but foo is the name of a *non*terminal — symbolic
    production references (like Perl's horrible globs as a cheap substitute
    for actual function references or lambdas.)
*   module syntax:
    
        module {
            prod = expr.
        }

*   module-level updatable variables.
*   turn system library back into built-in keywords (esp. if : can be used)
*   should be able to import ("open") other modules into your own namespace.
*   including files, library files should be **handled by the implementation**
*   EOF and nil are the same?  it would make sense... call it `end`?
*   regex-like shortcuts: `\w` for "word", `\s` for "whitespace", etc.
*   meta-circular implementation of compiler!
*   `$.unquote` should take left and right quotes to expect
*   define a stringify-repr operation on terms
*   Tamsin scanner: more liberal (every non-alphanum+_ symbol scans as itself,
    incl. ones that have no meaning currently like `*` and `?`)
*   use `←` instead of `@`, why not?
*   pattern match in send:
    *   `fields → F@fields(H,T) & H`
*   maps, implemented as hash tables.
    *   `Table ← {} & fields → F@fields(H,T) & Table[H] ← T`
*   on that topic — production values and/or lambda productions...
*   auto-generate terms from productions, like Rooibos does
*   `;` = `&`?
*   pretty-print AST for error messages
*   `$.alpha`
*   `$.digit`
*   don't consume stdin until asked to scan.
*   numeric values... somehow.  number('65') = #65.  decode(ascii, 'A') = #65.
*   token classes... somehow.  (then numeric is just a special token class?)
*   term expressions -- harder than it sounds
*   be generous and allow "xyz" in term context position?
*   non-backtracking versions of `|` and `{}`?  (very advanced)
*   «» could be an alias w/right sym (`,,`, `„`)
    (still need to scan it specially though)
*   special form that consumes rest of input from the Tamsin source -- gimmick
*   feature-testing: `$.exists('$.blargh') | do_without_blargh`
*   ternary: `foo ? bar : baz` -- if foo succeeded, do bar, else do baz.
*   a second implementation, in C -- with compiler to C and meta-circular
    implementation, this can be generated!
