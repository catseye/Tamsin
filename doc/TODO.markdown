TODO
----

*   turn system library back into built-in keywords (esp. if ¶ can be used)
*   better command-line argument parsing
*   `@include` -- for the scanner, especially
*   `$.unquote` should take left and right quotes to expect
*   define a stringify-repr operation on terms

### 8-bit clean/UTF-8 ###

*   8-bit clean strings, in both Python and C.  tests for these as string
    literals, ability to scan them on input, and ability to produce them
    on output.
*   arbitrary non-printable characters in terms and such
*   decode UTF-8 in compiled C code : character scanner yields one Unicode char
*   more tests for UTF-8

### meta-circularity/bootstrapping ###

*   meta-circular implementation of analyzer!
*   meta-circular implementation of compiler!
*   meta-circular implementation of interpreter!  (not so useful?)
*   figure out why compiled verstion of tamsin-ast hangs...

### lower-priority/experimental ###

*   Tamsin scanner: more liberal (every non-alphanum+_ symbol scans as itself,
    incl. ones that have no meaning currently like `/` and `?`)
*   use `←` instead of `@`, why not?
*   `¶foo` means production called `foo`, to disambiguate
    (this would mean unaliasing is less necessary -- call your production
    `¶return` if you like) -- ASCII version?  `p^foo`?
*   pattern match in send:
    *   `fields → F@fields(H,T) & H`
*   maps, implemented as hash tables.
    *   `Table ← {} & fields → F@fields(H,T) & Table[H] ← T`
*   global variables.  or better, variables scoped to a set of productions.
*   these idioms are so common there ought to be a form for them:
    *   `set A = '' & {rule → B & A ← A + B} & A`
    *   `set A = nil & {rule → B & A ← cons(A, B)} & A`
    indeed, this is a fold!  something like...
    *   `fold rule '' +`
    *   `fold rule nil cons`
    i.e.
    *   `"fold" & expr0 & term & ("+" | term)`
    that certainly implies that `+` is a constructor though.  hmmm...
    well, we could start with the term version, like:
    
        expr0 = expr1 → E & fold ("+" & expr1) E add.
        expr1 = term → E & fold ("*" & term) E mul.
        term = "x" | "y" | "z" | "(" & expr0 → E & ")" & E.

*   auto-generate terms from productions, like Rooibos does
*   `;` = `&`?
*   pretty-print AST for error messages
*   have analyzer, interpreter, compiler all inherit from ASTWalker or smth?
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