import unittest
import numpy as np

from process_timestamps import consolidate_beeps

class TestConsolidateBeeps(unittest.TestCase):
    def do_test(self,news_report):
        return consolidate_beeps(news_report)
    
    def test_zero_everything(self):
        result = self.do_test(news_report=[])
        np.testing.assert_array_equal(result,[])
        
    def test_only_one(self):
        result = self.do_test(news_report=[10])
        np.testing.assert_array_equal(result,[10])

    def test_no_repeat(self):
        result = self.do_test(news_report=[10,30,50,70])
        np.testing.assert_array_equal(result,[10,30,50,70])
        
    def test_repeat_beginning(self):
        result = self.do_test(news_report=[10,11,12,13,30,50,70])
        np.testing.assert_array_equal(result,[10,30,50,70])
        
    def test_repeat_middle(self):
        result = self.do_test(news_report=[10,30,31,32,33,50,70])
        np.testing.assert_array_equal(result,[10,30,50,70])

    def test_repeat_end(self):
        result = self.do_test(news_report=[10,30,50,70,71,72,73,74])
        np.testing.assert_array_equal(result,[10,30,50,70])
        
    def test_consecutive_good_ones_with_repeat(self):
        result = self.do_test(news_report=[10,30,50,51,52,53,70,71,72,73,74])
        np.testing.assert_array_equal(result,[10,30,50,70])
        

    def test_3_repeats(self):
        result = self.do_test(news_report=[11,12,13,14,30,50,70])
        np.testing.assert_array_equal(result,[11,30,50,70])

    def test_4_repeats(self):
        result = self.do_test(news_report=[11,12,13,14,15,30,50,70])
        np.testing.assert_array_equal(result,[11,30,50,70])

    def test_5_repeats(self):
        result = self.do_test(news_report=[11,12,13,14,15,16,30,50,70])
        np.testing.assert_array_equal(result,[11,30,50,70])
        
    def test_6_repeats(self):
        result = self.do_test(news_report=[11,12,13,14,15,16,17,30,50,70])
        np.testing.assert_array_equal(result,[11,17,30,50,70])
        

if __name__ == '__main__':
    unittest.main()