System Module
-------------

    -> Tests for functionality "Intepret Tamsin program"

The module `$` contains a number of built-in productions which would not
be possible or practical to implement in Tamsin.  See Appendix C for a list.

In fact, we have been using the `$` module already!  But our usage of it
has been hidden under some syntactic sugar.  For example, `"k"` is actually...

    | main = $:expect(k).
    + k
    = k

    | main = $:expect(k).
    + l
    ? expected 'k' but found 'l'

The section about aliases needs to be written too.

Here's `$:alnum`, which only consumes tokens where the first character is
alphanumeric.

    | main = "(" & {$:alnum → A} & ")" & A.
    + (abc123deefghi459876jklmnopqRSTUVXYZ0)
    = 0

    | main = "(" & {$:alnum → A} & ")" & A.
    + (abc123deefghi459876!jklmnopqRSTUVXYZ0)
    ? expected ')' but found '!'

Here's `$:upper`, which only consumes tokens where the first character is
uppercase alphabetic.

    | main = "(" & {$:upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNOPQRSTUVWXYZ)
    = Z

    | main = "(" & {$:upper → A} & ")" & A.
    + (ABCDEFGHIJKLMNoPQRSTUVWXYZ)
    ? expected ')' but found 'o'

Here's `$:startswith`, which only consumes tokens which start with
the given term.  (For a single-character scanner this isn't very
impressive.)

    | main = "(" & {$:startswith('A') → A} & ")" & A.
    + (AAAA)
    = A

    | main = "(" & {$:startswith('A') → A} & ")" & A.
    + (AAAABAAA)
    ? expected ')' but found 'B'

Here's `$:mkterm`, which takes an atom and a list and creates a constructor.

    | main = $:mkterm(atom, list(a, list(b, list(c, nil)))).
    = atom(a, b, c)

Here's `$:unquote`, which takes three terms, X, L and R, where L and R
must be atoms.  If X begins with L and ends with R then the contents
in-between will be returned as an atom.  Otherwise fails.

    | main = $:unquote('"hello"', '"', '"').
    = hello

    | main = $:unquote('(hello)', '(', ')').
    = hello

    | main = $:unquote('(hello)', '(', '"').
    ? term '(hello)' is not quoted with '(' and '"'

    | main = $:unquote('(hello)', '[', ')').
    ? term '(hello)' is not quoted with '[' and ')'

The quotes can be Unicode characters.

    | main = $:unquote('“hello”', '“', '”').
    = hello

The quotes can be multiple characters.

    | main = $:unquote('%-hello-%', '%-', '-%').
    = hello

The quotes can even be empty strings.

    | main = $:unquote('hello', '', '').
    = hello

Here's `$:equal`, which takes two terms, L and R.  If L and R are equal,
succeeds and returns that term which they both are.  Otherwise fails.

Two atoms are equal if their texts are identical.

    | main = $:equal('hi', 'hi').
    = hi

    | main = $:equal('hi', 'lo').
    ? term 'hi' does not equal 'lo'

Two constructors are equal if their texts are identical, they have the
same number of subterms, and all of their corresponding subterms are equal.

    | main = $:equal(hi(there), hi(there)).
    = hi(there)

    | main = $:equal(hi(there), lo(there)).
    ? term 'hi(there)' does not equal 'lo(there)'

    | main = $:equal(hi(there), hi(here)).
    ? term 'hi(there)' does not equal 'hi(here)'

    | main = $:equal(hi(there), hi(there, there)).
    ? term 'hi(there)' does not equal 'hi(there, there)'

Here's `$:emit`, which takes an atom and outputs it.  Unlike `print`, which
is meant for debugging, `$:emit` does not append a newline, and is 8-bit-clean.

    | main = $:emit('`') & $:emit('wo') & ''.
    = `wo

    -> Tests for functionality "Intepret Tamsin program (pre- & post-processed)"

`$:emit` is 8-bit-clean: if the atom contains unprintable characters,
`$:emit` does not try to make them readable by UTF-8 or any other encoding.
(`print` may or may not do this, depending on the implementation.)

    | main = $:emit('\x00\x01\x02\xfd\xfe\xff') & ''.
    = 000102fdfeff0a

    -> Tests for functionality "Intepret Tamsin program"

Here's `$:repr`, which takes a term and results in an atom which is the
result of reprifying that term (see section on Terms, above.)

    | main = $:repr(hello).
    = hello

    | main = $:repr('016fo_oZZ').
    = 016fo_oZZ

    | main = $:repr('016fo$oZZ').
    = '016fo$oZZ'

    | main = $:repr('').
    = ''

    | main = $:repr(' ').
    = ' '

    | main = $:repr('016\n016').
    = '016\x0a016'

    | main = $:repr(hello(there, world)).
    = hello(there, world)

    | main = V ← '♡' & $:repr('□'(there, V)).
    = '\xe2\x96\xa1'(there, '\xe2\x99\xa1')

    | main = $:repr(a(b(c('qu\'are\\')))).
    = a(b(c('qu\'are\\')))

    | main = $:repr('\x99').
    = '\x99'

Here's `$:reverse`, which takes a term E, and a term of the form
`X(a, X(b, ... X(z, E)) ... )`, and returns a term of the form
`X(z, X(y, ... X(a, E)) ... )`.  The constructor tag X is often `cons`
or `pair` or `list` and E is often `nil`.

    | main = $:reverse(list(a, list(b, list(c, nil))), nil).
    = list(c, list(b, list(a, nil)))

E need not be an atom.

    | main = $:reverse(list(a, list(b, list(c, hello(world)))), hello(world)).
    = list(c, list(b, list(a, hello(world))))

If the tail of the list isn't E, an error occurs.

    | main = $:reverse(list(a, list(b, list(c, hello(world)))), nil).
    ? malformed list

If some list constructor doesn't have two children, an error occurs.

    | main = $:reverse(list(a, list(b, list(nil))), nil).
    ? malformed list

The constructor tag can be anything.

    | main = $:reverse(foo(a, foo(b, foo(c, nil))), nil).
    = foo(c, foo(b, foo(a, nil)))

But if there is a different constructor somewhere in the list, well,

    | main = $:reverse(foo(a, fooz(b, foo(c, nil))), nil).
    ? malformed list

You can reverse an empty list.

    | main = $:reverse(nil, nil).
    = nil

But of course,

    | main = $:reverse(nil, zilch).
    ? malformed list

This is a shallow reverse.  Embedded lists are not reversed.

    | main = $:reverse(list(a, list(list(1, list(2, nil)), list(c, nil))), nil).
    = list(c, list(list(1, list(2, nil)), list(a, nil)))

Here's `$:gensym`.

    | main = $:gensym('foo').
    = foo1

    | main = $:gensym('foo') → F & $:gensym('foo') → G & $:equal(F, G).
    ? 'foo1' does not equal 'foo2'

Here's `$:hexbyte`.

    | main = $:hexbyte('5', '0').
    = P

    | main = $:hexbyte('f', 'f') → C & $:repr(C).
    = '\xff'

Here's `$:format_octal`, which makes me feel ill.

    | main = $:format_octal('P').
    = 120

    | main = $:format_octal('\xff').
    = 377

There are never any leading zeroes.

    | main = $:format_octal('\n').
    = 12

It works on the first byte of the string only.

    | main = $:format_octal('«').
    = 302

Here's `$:length`, which returns an atom representing the length, in bytes,
of the given term (flattened.)  Note that this is an atom, not an integer,
because Tamsin doesn't even have integers.

    | main = $:length(abcde).
    = 5

    | main = $:length('').
    = 0

    | main = $:length('♥').
    = 3

    | main = $:length(a(   b  ,  c  )).
    = 7
