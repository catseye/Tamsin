TODO
----

*   `$:deep_reverse`
*   use Tamsin repr in error messages
*   definition of reprification needs work (e.g. `"` should repr to `'"'`)
*   python impl should take >1 source file on cmdline (external modules)

### more tests ###

*   tests that `'V'` is not a variable and that `'EOF'` is not EOF
*   tests for failing when utf8 scanner hits badly-encoded utf8

### vm support ###

*   `$:add`, `$:sub`, `$:mul`, `$:div`, `$:rem`, for atoms which look like
    integers: `["-"] & {$:digit}`.
*   `$:tell` and `$:seek` the implicit buffer -- for VM's etc -- although
    note, this may have scary consequences when combined with backtracking
*   non-backtracking versions of `|` and `{}`?  `~|` and `~{}`
*   `$.alpha`
*   `$.digit`

### lower-priority ###

*   make it possible to recover from more errors using `|` (don't throw
    exceptions so often)
*   fold: often you want to construct terms "the other way" or to "join"
    a string with delimiters; can we handle those cases too?
*   stronger tests for scanner, parser: dump all falderal testbodies to files
*   option for ref interp to not output result (or by default, don't)
*   "mini" interpreter that handles variables (ouch)
*   SOME WAY TO DISTINGUISH PRODUCTIONS WHICH MAY CONSUME INPUT AND
    PRODUCTIONS WHICH NEVER CONSUME INPUT (in the `$` module, and generally).
*   actual numeric values, rather than atoms-which-contain-only-digits
*   error reporting: line number
*   error handling: skip to next sentinel and report more errors
*   module-level updatable variables.
*   `using` production x: x's scanner defaults to utf8, not x
*   figure out good way to do aliases with the Tamsin-parser-in-Tamsin
    (dynamic grammar is really more of a Zz thing...)
*   should be able to import ("open") other modules into your own namespace.
*   meta-circular implementation of compiler!
*   `@` a la Haskell in pattern-match:
    *   `walk(T@tree(L,R)) = ...`
*   pattern match in send:
    *   `fields → fields(H,T) & H`
*   maps, implemented as hash tables.
    *   `Table ← {} & fields → F@fields(H,T) & Table[H] ← T`
*   on that topic — production values and/or lambda productions...
*   pretty-print AST for error messages
*   don't consume stdin until asked to scan.
*   full term expressions -- maybe

### symbol fun ###

*   `~` (Lua) for not and `!` (Prolog) for non-backtracking?
*   lowercase greek letters are variables too!
*   use `←` instead of `@`, why not?
*   `;` = `&`?
*   be generous and allow `"xyz"` in term context position?
*   denotational semantics sugar!  something like...
    
        ⟦add α β⟧ = $:add(⟦α⟧, ⟦β⟧).
    
    and/or

        ⟦add α β⟧(σ) = $:add(⟦α⟧(σ), ⟦β⟧(σ)).
        ⟦var α⟧(σ) = fetch(σ, α).

    of course, DS is a bit fast-and-loose about actual parsing...
    but the syntax looks mighty fine.

### wild ideas ###    

*   regex-like shortcuts: `\w` for "word", `\s` for "whitespace", etc.
*   EOF and nil are the same?  it would make sense... call it `end`?
*   productions with names with arbitrary characters in them.
*   something like «foo» but foo is the name of a *non*terminal — symbolic
    production references (like Perl's horrible globs as a cheap substitute
    for actual function references or lambdas.)
*   turn system library back into built-in keywords (esp. if : can be used)
*   Tamsin scanner: more liberal (every non-alphanum+_ symbol scans as itself,
    incl. ones that have no meaning currently like `*` and `?`)
*   auto-generate terms from productions, like Rooibos does
*   token classes... somehow.  (then numeric is just a special token class?)
    a token class is just the "call stack" of productions at the time it
    was scanned
*   «» could be an alias w/right sym (`,,`, `„`)
    (still need to scan it specially though)
*   special form that consumes rest of input from the Tamsin source --
    maybe not such a gimmick since micro-tamsin does this
*   feature-testing: `$.exists(module) | do_without_module`
*   ternary: `foo ? bar : baz` -- if foo succeeded, do bar, else do baz.
