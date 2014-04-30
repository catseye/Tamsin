These are now out of context, and kept here for historical purposes.

### an aside, written a while back ###

OK!  So... here is a problem: if you haven't noticed yet,

*   what a rule consumes, is a string.
*   what a rule evaluates to, is a term.
*   the symbol `(` means something different in a rule (where it expresses
    precendence) than in a term (where it signifies the list of subterms.)
*   the symbol `foo` means something different in a rule (where it denotes
    a production) than in a term (where it is an atom.)

This is probably unacceptable.  Which syntax do we want to change?

    PRODUCTION = set V = foo & return ⟨atom V production⟩.

i.e. productions are distinguished from atoms and variables by being
all-caps.  Lists are distinguished from precedence by being ⟨ ⟩.

    production = set V = 'foo & return '(atom V production).

i.e. `'` acts a bit like quote, or rather quasi-quote, as Variables get
expanded.

    production = set V = :foo & return :smth(:atom Var :production).

i.e. atoms are prefixed with `:`, like Ruby, and terms are constructors
with a leading atom, like real terms and not like lists.

    production = set V = 「foo」 & return 「(atom Var anotheratom)」.

A funky, Japanese-influenced version of quote.  Nice, but really not suited
for this, quite.  Ditto ⟦these⟧.

Ah, well, it may not be a real problem, unless we want to make `return`
optional (which we do.)  Maybe, onto weirder stuff first.

### stuff about implicit buffer ###

Here's a "problem": the implicit buffer is a string, and we don't have
strings in the data domain, we have terms.  This "problem" is easily
"solvable": we can stringify the term.  This is a terrible "solution",
but it lets us experiment further.

This would be nicer if we had a syntax to put arbitrary text in an atom.
Hey, how about 「this is an atom」?  Hmmm...

#### A prolix note on implementation ####

Traditionally, scanners for recursive descent parsers pre-emptively scan
the next token.  This was done because originally, parsers (for languages
like Pascal, say,) were distinctly one-pass beasts, reading the source code
off of a stream from disk (or maybe even from a tape), and you might need
to refer to the current token several times in the code and you don't want
to have to read it more than once.

This setup makes writing a parser with a "hot-swappable" scanner tricky,
because when we switch scanner, we have to deal with this "cached" token
somehow.  We could rewind the scanner by the length of the token (plus
the length of any preceding whitespace and comments), switch the scanner,
then scan again (by the new rules.)  But this is messy and error-prone.

Luckily, not many of us are reading files off tape these days, and we have
plenty of core, so it's no problem reading the whole file into memory.
In fact, I've seen it argued that the best way to write a scanner nowadays
is to `mmap()` the file.  We don't do this in the implementation of Tamsin,
but we do read the entire file into memory.

This makes the cache-the-next-token method less useful, and so we don't
do it.  Instead, we look for the next token only when we need it, and we
have a method `peek()` that returns what the next token would be, and we
don't cache this value.

There are a couple of other points about the scanner implementation.
A scanner only ever has one buffer (the entire string it's scanning); this
never changes over it's lifetime.  It provides methods for saving and
restoring its state, and it has a stack of "engines" which provide the
actual scanning logic.  In addition, there is only one interpreter object,
and it only has one scanner object during its lifetime.

### Implementation Notes ###

Maybe test-driven language design *not* "for the win" in all cases; it's
excellent for evolving a design, but not so good for deep debugging.  I had
to actually write a dedicated test case which directly accessed the internals,
to find the problem.

This was only after refactoring the implementation two or three times.  One
of those times, I removed exceptions, so now the interpreter returns
`(success, result)` tuples, where `success` is a boolean, and propagates
parse errors itself.

We "raise" a parse error only in the `LITERAL` AST node.

We handle parse errors (backtrack) only in `OR` and `WHILE`, and in the
ProductionScannerEngine logic (to provide that EOF if the scanning production
failed.  This can happen even in `peek()` at the end of a string, even after
we've successfully parsed everything else.)

### aside #2 ###

Well this is all very nice, very pretty I'm sure you'll agree, but it doesn't
hang together too well.  Figuration is easier than composition.  The thing is
that we still have these two domains, the domain of strings that we parse
and the domain of terms that we match.  We need to bring them closer together.
This section is just ideas for that.

One is that instead of, or alongside terms, we compose strings.

First, we put arbitrary text in an atom, with `「this syntax」`.  Then we allow
terms to be concatenated with `•`.  It looks real cool!  But also, it's kind
of annoying.  So we also allow `'this ' + 'syntax.'`.

### ... ###

Indeed we can.

The next logical step would be to be able to say

    main = program using scanner.
    scanner = scan using ☆char.
    scan = {" "} & (...)
    program = "token" & ";" & "token" & ...

But we're not there yet.

Well, the best way to get there is to make that a test, see it fail, then
improve the implementation so that it passes,  Test-driven language design
for the win!  (But maybe not in all cases.  See my notes below...)

### ... #2 ###

Having thought more about it, I think the easiest way to reconcile terms
and strings is to have terms be syntactic sugar for strings.  This is
already the case for ground terms, since `tree(a,b)` stringifies to the
same string as `「tree(a,b)」`.  It's when variables are involved where it
differs.  We would like some kind of quasi-quote such that even though
`「tree(A,b)」` → `tree(A,n)`, `«tree(A,b)»` → `tree(tree(x,y),b)` or
whatever.

Although, I still don't know.  The thing about terms is that they are
super-useful for intermediate representations — abstract syntax trees
and the like.  I've been thinking about some kind of compromise.  Which
is, currently, what we sort of have.  A Tamsin term doubles as a string,
for better or worse.  Mainly, we should sort out the properties of terms,
then.  Which we will do.  But first,
