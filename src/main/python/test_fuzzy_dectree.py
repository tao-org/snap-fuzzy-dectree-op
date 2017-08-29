import os
import unittest

import sys
import numpy as np

# noinspection PyUnresolvedReferences
class TestFuzzyDectree(unittest.TestCase):
    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.normpath(os.path.dirname(__file__)))
        print('parentDir: ', self.parent_dir)

    def test_numpy_compare(self):
        a1 = np.array([1.0, 3.0, 0.0, 2.0])
        a2 = np.array([0.0, 5.0, 0.0, 0.0])
        a3 = np.array([2.0, 0.0, 0.0, 4.0])
        samples = [a1, a2, a3]

        max = np.empty(4)
        max.fill(sys.float_info.min)
        max_index = np.empty(4, dtype=np.int16)
        max_index.fill(0)
        j = 0
        for sample in samples:
            x = np.where(sample > max)
            max[x] = sample
            if sample > max:
                max = sample
                max_index = j
            j += 1
        print('max_index: ', max_index)


print ('Testing fuzzy dectree')
suite = unittest.TestLoader().loadTestsFromTestCase(TestFuzzyDectree)
unittest.TextTestRunner(verbosity=2).run(suite)
