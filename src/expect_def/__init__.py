import io
import re
import os
import sys
import inspect
import contextlib
import subprocess
from typing import cast, Any
from dataclasses import dataclass
from collections import defaultdict


EXPECTATIONS = defaultdict(list)

@dataclass
class Expectation:
    f: Any # TODO: describe the function type
    line_number: int

    def __post_init__(self):
        self.name = self.f.__name__
        self.module = self.f.__module__
        self.file = inspect.getfile(self.f)
        self.expected = self.f.__doc__
        self.has_doc_string = self.expected is not None

    def run(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with contextlib.redirect_stderr(output):
                self.f()
        self.result = output.getvalue()


        def strip_whitespace(s):
            if s is None:
                return None
            return "\n".join([ l.strip() for l in s.splitlines()]).strip()


        return strip_whitespace(self.result) == strip_whitespace(self.expected)
    
    def get_indent(self):
        sourcelines = inspect.getsourcelines(self.f)[0]
        for i, line in enumerate(sourcelines):
            if line.lstrip().startswith("def"):
                firstline = sourcelines[i + 1]
                return firstline.removesuffix(firstline.lstrip())



def caller_line_number():
    return cast(Any, inspect.stack()[2]).positions.lineno

def test(f):
    expectation = Expectation(f, line_number=caller_line_number())
    EXPECTATIONS[expectation.file].append(expectation)
    return f

doc_comment_regex = re.compile(r'\s"""')
function_def_regex = re.compile(r'def \w+\(')

def write_corrected_file(file, expectations):
    expectations_by_line = {}
    for expectation in expectations:
        # each expectation should have its own line in this file
        # (and line numbers are 1-indexed)
        expectations_by_line[expectation.line_number - 1] = expectation

    errfile = file + ".err"

    with open(file) as infile:
        with open(errfile, "w") as outfile:

            state = "reading"
            expectation = None

            for i, line in enumerate(infile.readlines()):
                keep_line = True

                if state == "reading" and expectations_by_line.get(i):
                    expectation = expectations_by_line[i]
                    state = "look for function def"

                if state == "look for function def" and function_def_regex.search(line):
                    indent = expectation.get_indent()
                    outfile.write(line)
                    outfile.write(indent + '"""\n')

                    for result_line in expectation.result.splitlines(True):
                        outfile.write(indent + result_line)
                    outfile.write(indent + '"""\n')
                    keep_line = False

                    if expectation.has_doc_string:
                        state = "skip next two doc comments"

                elif state == "skip next two doc comments" and doc_comment_regex.search(line):
                    keep_line = False
                    state = "skip next doc comment"
                elif state == "skip next doc comment" and doc_comment_regex.search(line):
                    keep_line = False
                    state = "reading"
                elif state == "skip next two doc comments" or state == "skip next doc comment":
                    keep_line = False

                if keep_line:
                    outfile.write(line)

    return errfile

def _run_accept():
    for file in EXPECTATIONS:
        errfile = file + ".err"
        if os.path.isfile(errfile):
            os.rename(errfile, file)

def _run_tests():
    # TODO: supporting filtering by module

    for file, expectations in EXPECTATIONS.items():
        errfile = file + ".err"
        if os.path.isfile(errfile):
            os.remove(errfile)

        file_success = all(list(map(lambda e: e.run(), expectations)))

        if file_success:
            print(f"{file} passed")
        else:
            print(f"{file} failed")
            errfile = write_corrected_file(file, expectations)
            subprocess.run(["patdiff", "-keep-whitespace", "-context", "3", file, errfile])


def run():
    """
    `run` runs all of the expectations matching supplied ARGV

    The standard usage is to create a test.py that first imports any modules
    whose tests you would like to be available (using @expect.test to define the tests)
    and then calls this function.
    """
    import argparse

    parser = argparse.ArgumentParser("test.py")
    parser.add_argument("action", choices=['test', 'accept'], default='test')
    args = parser.parse_args()

    if args.action == 'test':
        return _run_tests()
    elif args.action == 'accept':
        return _run_accept()
    else:
        raise argparse.ArgumentTypeError


expect = sys.modules[__name__]

@expect.test
def first_test():
    """
    a
    b
    b
    b
    b
    c
    """
    print("a")
    for _ in range(4):
        print("b")
    print("c")


def extra_decorator(a):
    from functools import wraps
    # so long as the decorator use `wraps` the generated expectation
    # will have the right indentation
    @wraps(a)
    def w():
        return a()
    return w

@expect.test
@extra_decorator
def test_with_extra_decorator():
    """
    hi there!
    """
    print("hi there!")
