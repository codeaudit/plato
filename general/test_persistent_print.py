from general.persistent_print import capture_print, read_print

__author__ = 'peter'


def test_persistent_print():

    capture_print(to_file=True)
    print 'aaa'
    print 'bbb'
    assert read_print()  == 'aaa\nbbb\n'
    capture_print(False)

    capture_print(True)
    assert read_print() == ''
    print 'ccc'
    print 'ddd'
    assert read_print()  == 'ccc\nddd\n'


if __name__ == '__main__':

    test_persistent_print()
