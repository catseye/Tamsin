TODO
----

*   analyzer needs to resolve module '' → current module
*   including files, library files should be **handled by the implementation**
*   document, too, the implementation-dependent nature of input and output
*   define a stringify-repr operation on terms
*   stronger tests for scanner, parser: dump all falderal testbodies to files
*   `emit` alongside `print`.
*   `emit` must be 8-bit clean, i.e. can emit `\x00`
*   tests for `emit`
*   option for ref interp to not output result (or by default, don't)
*   "fakie" interpreter

### lower-priority/experimental ###

*   error reporting: line number
*   error handling: skip to next sentinel and report more errors
*   regex-like shortcuts: `\w` for "word", `\s` for "whitespace", etc.
*   EOF and nil are the same?  it would make sense... call it `end`?
*   module-level updatable variables.
*   tests for failing when utf8 scanner hits badly-encoded utf8
*   numeric values... somehow.  number('65') = #65.  decode(ascii, 'A') = #65.
*   tell/rewind the implicit buffer -- for VM's etc
*   `using` production x: x's scanner defaults to utf8, not x
*   figure out good way to do aliases with the Tamsin-parser-in-Tamsin
    (dynamic grammar is really more of a Zz thing...)
*   productions with names with arbitrary characters in them.
*   something like «foo» but foo is the name of a *non*terminal — symbolic
    production references (like Perl's horrible globs as a cheap substitute
    for actual function references or lambdas.)
*   turn system library back into built-in keywords (esp. if : can be used)
*   should be able to import ("open") other modules into your own namespace.
*   meta-circular implementation of compiler!
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
