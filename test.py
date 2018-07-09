import unittest
from in_working_time import compute_working_time
from dateutil import parser


class TestComputeTime(unittest.TestCase):
    def test_compute_friday_working_time(self):
        _start = '06.07.18 16:00'
        _end = '09.07.18 10:30'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 8100)
    
    def test_compute_months_working_time(self):
        _start = '28.06.18 16:00'
        _end = '03.07.18 8:50'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 61500)

    def test_next_day(self):
        _start = '02.04.2018  19:00:02'
        _end = '03.04.2018  8:36:31'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 360)
    
    def test_lunch(self):
        _start = '02.04.2018  12:30:00'
        _end = '02.04.2018  12:45:00'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 0)
    
    def test_holiday(self):
        _start = '28.04.2018  10:50:00'
        _end = '28.04.2018  10:54:00'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 240)    
    
    def test_forced_close(self):
        _start = '02.04.2018 10:10'
        _end = '16.04.2018  14:45:06'
        result = compute_working_time(_start, _end, True)
        self.assertEqual(result, 301800)
        
if __name__ == '__main__':
    unittest.main()