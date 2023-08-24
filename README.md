# expect-def

[![PyPI - Version](https://img.shields.io/pypi/v/expect-def.svg)](https://pypi.org/project/expect-def)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/expect-def.svg)](https://pypi.org/project/expect-def)

-----

## Motivation

Expect tests give you a repl-like interactive development experience where any manual tests you make are trivially turned into automated assertions. The process of changing these assertions to match new constraints is as easy as can be.

See Jane Street's blog post [The Joy of Expect Tests](https://blog.janestreet.com/the-joy-of-expect-tests/).

## Usage

Create a test like so:

```
import expect_def as expect

@expect.test
def test_five_times_five():
    print(5 * 5)
```

This can be in a file specifically for testing or right next to the code it is testing.
Anything you print will become an assertion

To run it, create a `test.py` file in the root of your project:

```
import src.your_project_here
import expect_def
expect_def.run
```

Make sure to import any modules whose tests you would like to run.


Runing `python test.py test` will show you a diff of the expected output if the tests fails:

```diff
/Users/charles/code/python-expect-def/src/expect_def/__init__.py passed
/Users/charles/code/python-expect-def/example/__init__.py failed
4a5,7
>     """
>     25
>     """
```

Which you can accept with `python test.py accept`.

## Alternatives

See also [snapshottest](https://pypi.org/project/snapshottest/) and [expecttest](https://pypi.org/project/expecttest/) and [pytest-expect](https://pypi.org/project/pytest-expect/). These don't make use of doc strings as a 

## Installation

```console
pip install expect-def
```

`expect-def` also depends on [patdiff](https://github.com/janestreet/patdiff) to show diffs, make sure to have that on the PATH.

## License

`expect-def` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
