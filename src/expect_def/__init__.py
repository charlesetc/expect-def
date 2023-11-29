import io
import re
import os
import inspect
import contextlib
import subprocess
import traceback
from typing import Literal, Optional, Callable as Fn
from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Iterable


@dataclass
class Expectation:
    f: Fn[[], None]
    line_number: int

    def __post_init__(self) -> None:
        self.name = self.f.__name__
        self.module = self.f.__module__
        self.file = inspect.getfile(self.f)
        self.expected = self.f.__doc__
        self.has_doc_string = self.expected is not None
        self.result = ""

    def run(self) -> bool:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            with contextlib.redirect_stderr(output):
                try:
                    self.f()
                except:
                    traceback.print_exc()

        self.result = output.getvalue() or ""

        def strip_whitespace(s: Optional[str]):
            if s is None:
                return None
            return "\n".join([l.strip() for l in s.splitlines()]).strip()

        return strip_whitespace(self.result) == strip_whitespace(self.expected)

    def get_indent(self) -> Optional[str]:
        sourcelines = inspect.getsourcelines(self.f)[0]
        for i, line in enumerate(sourcelines):
            if line.lstrip().startswith("def"):
                firstline = sourcelines[i + 1]
                return firstline.removesuffix(firstline.lstrip())


EXPECTATIONS: defaultdict[str, list[Expectation]] = defaultdict(list)


def caller_line_number() -> int:
    positions = inspect.stack()[2].positions
    assert positions is not None
    line_number = positions.lineno
    assert line_number is not None
    return line_number


def test(f: Fn[[], None]) -> Fn[[], None]:
    expectation = Expectation(f, line_number=caller_line_number())
    EXPECTATIONS[expectation.file].append(expectation)
    return f


ExpectationState = Literal[
    "reading",
    "look for function def",
    "skip next two doc comments",
    "skip next doc comment",
]


doc_comment_regex = re.compile(r'\s"""')
double_doc_comment_regex = re.compile(r'\s""".*\s"""')
function_def_regex = re.compile(r'def \w+\(')


def write_corrected_file(file: str, expectations: Iterable[Expectation]) -> str:
    expectations_by_line: dict[int, Expectation] = {}
    for expectation in expectations:
        # each expectation should have its own line in this file
        # (and line numbers are 1-indexed)
        expectations_by_line[expectation.line_number - 1] = expectation

    errfile = file + ".err"

    with open(file) as infile:
        with open(errfile, "w") as outfile:
            state: ExpectationState = "reading"
            expectation: Optional[Expectation] = None

            for i, line in enumerate(infile.readlines()):
                keep_line = True

                if state == "reading" and expectations_by_line.get(i):
                    expectation = expectations_by_line[i]
                    state = "look for function def"

                elif state == "look for function def" and function_def_regex.search(line):
                    assert expectation is not None
                    indent = expectation.get_indent()
                    assert indent is not None
                    outfile.write(line)
                    outfile.write(indent + '"""\n')

                    for result_line in expectation.result.splitlines(True):
                        outfile.write(indent + result_line)
                    outfile.write(indent + '"""\n')
                    keep_line = False

                    if expectation.has_doc_string:
                        state = "skip next two doc comments"

                elif state == "skip next two doc comments" and double_doc_comment_regex.search(line):
                    keep_line = False
                    state = "reading"

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


def _run_accept() -> None:
    for file in EXPECTATIONS:
        errfile = file + ".err"
        if os.path.isfile(errfile):
            os.rename(errfile, file)


def _run_tests() -> None:
    # TODO: supporting filtering by module

    for file, expectations in EXPECTATIONS.items():
        errfile = file + ".err"
        if os.path.isfile(errfile):
            os.remove(errfile)

        file_success = all(map(lambda e: e.run(), expectations))

        if file_success:
            print(f"{file} passed")
        else:
            print(f"{file} failed")
            errfile = write_corrected_file(file, expectations)
            print(f"diff {file} {errfile}")
            subprocess.run(["patdiff", "-keep-whitespace", "-context", "3", file, errfile])


def run() -> None:
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
