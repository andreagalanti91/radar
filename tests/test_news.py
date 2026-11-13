import datetime as dt
import unittest

from radar.news import fomc_time_rome


class FomcOraTest(unittest.TestCase):


    def test_fomc_time_rome_regular(self):
        self.assertEqual(fomc_time_rome(dt.date(2026, 1, 28)), "20:00")
        self.assertEqual(fomc_time_rome(dt.date(2026, 7, 29)), "20:00")
        self.assertEqual(fomc_time_rome(dt.date(2026, 12, 9)), "20:00")


    def test_fomc_time_rome_dst_gap(self):
        # USA già in ora legale, Europa non ancora (marzo) / Europa già in ora solare, USA no (fine ottobre-inizio novembre)
        self.assertEqual(fomc_time_rome(dt.date(2026, 3, 18)), "19:00")
        self.assertEqual(fomc_time_rome(dt.date(2026, 10, 28)), "19:00")
        self.assertEqual(fomc_time_rome(dt.date(2025, 10, 29)), "19:00")


if __name__ == "__main__":
    unittest.main()
