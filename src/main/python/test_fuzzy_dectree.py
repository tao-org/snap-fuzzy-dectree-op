import os
import unittest

import numpy as np

INTERTIDAL_FLAT_CLASSIF = np.array([[8, 255, 0, 0],  # Muschel, final class + RGB code
                                       [13, 255, 113, 255],  # Schill
                                       [1, 255, 255, 75]])  # Sand

INTERTIDAL_FLAT_CLASSIF_2 = np.array([8, 13, 1])

# noinspection PyUnresolvedReferences
class TestFuzzyDectree(unittest.TestCase):
    def setUp(self):
        self.parent_dir = os.path.dirname(os.path.normpath(os.path.dirname(__file__)))
        print('parentDir: ', self.parent_dir)

    def test_numpy_compare(self):
        a1 = np.array([1.0, 3.0, 1.0, 2.0])
        a2 = np.array([0.0, 5.0, 0.0, 0.0])
        a3 = np.array([2.0, 0.0, 0.0, 4.0])
        samples = [a1, a2, a3]
        samples2d = np.array(samples)
        # samples2dswap = np.swapaxes(samples2d, 0, 1)
        # i0 = np.argmax(samples2dswap[0])
        # i1 = np.argmax(samples2dswap[1])
        # i2 = np.argmax(samples2dswap[2])
        # i3 = np.argmax(samples2dswap[3])
        # ii = np.array([i0, i1, i2, i3])
        #
        # print('ii: ', ii)

        # jj = np.argmax(samples2dswap, axis=1)
        kk = np.argmax(samples2d, axis=0)
        print('kk: ', kk)

        final_class_data = INTERTIDAL_FLAT_CLASSIF_2[kk]
        print('final_class_data: ', final_class_data)


print ('Testing fuzzy dectree')
suite = unittest.TestLoader().loadTestsFromTestCase(TestFuzzyDectree)
unittest.TextTestRunner(verbosity=2).run(suite)
