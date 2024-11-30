import unittest
import numpy as np

from audio_offset_finder_v2.peak_methods import find_closest_troughs


class TestPeakMethods(unittest.TestCase):

    @unittest.skip(
        reason="This test is not implemented")
    def test_zero_everything(self):
        result = self.do_test(intros=[],
                              backup_intro_ts=[],
                              news_reports=[])
        np.testing.assert_array_equal(result,
                                      [])

    def test_find_closest_troughs_no_peak(self):
        data = [10,20,30,40,50]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [len(data)-1,len(data)-1])

    def test_find_closest_troughs_no_peak2(self):
        data = [50,40,30,20,10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [0,0])

    def test_find_closest_troughs_in_middle(self):
        data = [10,20,5,30,50,40,25,30,20]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [2,6])

    def test_find_closest_troughs_at_both_end(self):
        data = [1,2,3,5,4,3,2]
        result = find_closest_troughs(peak_index=3,data=data)
        np.testing.assert_array_equal(result,
                                      [0,len(data)-1])

    def test_find_closest_troughs_at_left_end_and_middle_right(self):
        data = [10,20,25,30,50,40,30,25,28,20]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [0,7])

    def test_find_closest_troughs_at_left_middle_and_right_end(self):
        data = [10,20,25,23,30,50,40,30,25,20,10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [3,len(data)-1])

    def test_find_closest_troughs_at_both_end(self):
        data = [1,2,3,5,4,3,2]
        result = find_closest_troughs(peak_index=3,data=data)
        np.testing.assert_array_equal(result,
                                      [0,len(data)-1])

    def test_find_closest_troughs_at_left_end_and_middle_right(self):
        data = [10,20,25,30,50,40,30,25,28,20]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [0,7])

    def test_find_closest_troughs_at_left_second_and_right_second(self):
        data = [10,5,25,28,30,50,40,30,25,20,4,10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [1,len(data)-2])

    def test_find_closest_troughs_at_left_second_and_right_middle(self):
        data = [10,5,25,28,30,50,40,30,25,10,15,10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [1,9])

    def test_find_closest_troughs_at_left_middle_and_right_second(self):
        data = [10,20,15,28,30,50,40,30,25,20,4,10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [2,len(data)-2])

    def test_flat(self):
        data = [10,10,15,28,30,50,40,30,25,20,20,21]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [0,len(data)-2])

    def test_flat2(self):
        data = [22, 21, 20, 20, 25, 30, 40, 50, 30, 28, 15, 10, 10]
        result = find_closest_troughs(peak_index=np.argmax(data),data=data)
        np.testing.assert_array_equal(result,
                                      [2,len(data)-1])

if __name__ == '__main__':
    unittest.main()