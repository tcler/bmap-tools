""" This test verifies Fiemap module functionality. It generates random sparse
files and make sure FIEMAP returns correct information about the holes. """

# Disable the following pylint recommendations:
#   *  Too many public methods - R0904
# pylint: disable=R0904

import unittest
import itertools

import tests.helpers
from bmaptools import Fiemap

class Error(Exception):
    """ A class for exceptions generated by this test. """
    pass

def _check_ranges(f_image, fiemap, first_block, blocks_cnt,
                  ranges, ranges_type):
    """ This is a helper function for '_do_test()' which compares the correct
    'ranges' list of mapped or unmapped blocks ranges for file object 'f_image'
    with what the Fiemap module reports. The 'ranges_type' argument defines
    whether the 'ranges' list is a list of mapped or unmapped blocks. The
    'first_block' and 'blocks_cnt' define the subset of blocks in 'f_image'
    that should be verified by this function. """

    if ranges_type is "mapped":
        fiemap_iterator = fiemap.get_mapped_ranges(first_block, blocks_cnt)
    elif ranges_type is "unmapped":
        fiemap_iterator = fiemap.get_unmapped_ranges(first_block, blocks_cnt)
    else:
        raise Error("incorrect list type")

    iterator = itertools.izip_longest(ranges, fiemap_iterator)

    for correct, check in iterator:
        if check[0] > check[1] or check != correct:
            raise Error("bad or unmatching %s range for file '%s': correct " \
                        "is %d-%d, get_%s_ranges(%d, %d) returned %d-%d" \
                        % (ranges_type, f_image.name, correct[0], correct[1],
                           ranges_type, first_block, blocks_cnt,
                           check[0], check[1]))

def _do_test(f_image, mapped, unmapped, buf_size = Fiemap.DEFAULT_BUFFER_SIZE):
    """ Verifiy that Fiemap reports the correct mapped and unmapped areas for
    the 'f_image' file object. The 'mapped' and 'unmapped' lists contain the
    correct ranges. The 'buf_size' argument specifies the internal buffer size
    of the 'Fiemap' class. """

    # Make sure that Fiemap's get_mapped_ranges() returns the same ranges as
    # we have in the 'mapped' list.
    fiemap = Fiemap.Fiemap(f_image, buf_size)
    first_block = 0
    blocks_cnt = fiemap.blocks_cnt

    _check_ranges(f_image, fiemap, first_block, blocks_cnt, mapped, "mapped")
    _check_ranges(f_image, fiemap, first_block, blocks_cnt, unmapped,
                  "unmapped")

class TestCreateCopy(unittest.TestCase):
    """ The test class for this unit tests. Basically executes the '_do_test()'
    function for different sparse files. """

    @staticmethod
    def test():
        """ The test entry point. Executes the '_do_test()' function for files
        of different sizes, holes distribution and format. """

        # Delete all the test-related temporary files automatically
        delete = True
        # Create all the test-related temporary files in the default directory
        # (usually /tmp).
        directory = None
        # Maximum size of the random files used in this test
        max_size = 16 * 1024 * 1024

        iterator = tests.helpers.generate_test_files(max_size, directory,
                                                     delete)
        for f_image, mapped, unmapped in iterator:
            _do_test(f_image, mapped, unmapped)
            _do_test(f_image, mapped, unmapped, Fiemap.MIN_BUFFER_SIZE)
            _do_test(f_image, mapped, unmapped, Fiemap.MIN_BUFFER_SIZE * 2)
            _do_test(f_image, mapped, unmapped, Fiemap.DEFAULT_BUFFER_SIZE / 2)
            _do_test(f_image, mapped, unmapped, Fiemap.DEFAULT_BUFFER_SIZE * 2)
