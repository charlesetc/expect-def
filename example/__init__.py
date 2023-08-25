import src.expect_def as expect


@expect.test
def test_five_times_five():
    """
    25
    """
    print(5 * 5)
