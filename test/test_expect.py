import src.expect_def as expect


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
def test_exception():
    """
    Traceback (most recent call last):
      File "/Users/charles/code/python-expect-def/src/expect_def/__init__.py", line 32, in run
        self.f()
      File "/Users/charles/code/python-expect-def/test/test_expect.py", line 43, in test_exception
        raise Exception("hi there!")
    Exception: hi there!
    """

    raise Exception("hi there!")


@expect.test
@extra_decorator
def test_with_extra_decorator():
    """
    hi there!
    """
    print("hi there!")
