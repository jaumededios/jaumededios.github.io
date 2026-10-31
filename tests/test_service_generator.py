"""Offline regression tests for the live site's service renderer."""
import importlib.util
import unittest
import io
import tempfile
from unittest.mock import patch
from urllib.parse import urlparse, parse_qs
from pathlib import Path

spec = importlib.util.spec_from_file_location("generate_cv", Path(__file__).resolve().parents[1] / "scripts" / "generate_cv.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

class ServiceTests(unittest.TestCase):
    def test_service_roles_not_called_reviewing(self):
        result = cv.gen_service([{'type': 'Co-organizer', 'details': 'PA²IN (upcoming)', 'year': '2027'}, {'type': 'Board member', 'details': 'Palomar', 'year': '2026–present'}])
        self.assertIn('\\section{Service}', result)
        self.assertIn('\\textbf{Co-organizer}', result)
        self.assertIn('upcoming', result)
        self.assertIn('Reviewer for: Transactions', result)
        self.assertNotIn('Reviewer for: PA', result)

    def test_explicit_reviewers_replace_fallback(self):
        result = cv.gen_service([{'type': 'Referee', 'details': 'Journal X', 'year': ''}])
        self.assertIn('Reviewer for: Journal X.', result)
        self.assertNotIn('Transactions', result)

    def test_placeholder_keeps_legacy_fallback(self):
        result = cv.gen_service([{'type': '(to be populated)', 'details': 'Add reviewing and service activities'}])
        self.assertIn('\\section{Reviewing}', result)
        self.assertIn('Reviewer for: Transactions', result)

class HeaderTests(unittest.TestCase):
    def test_required_headers_still_reject_malformed_csv(self):
        with self.assertRaises(SystemExit):
            cv.read_records('grants_awards', 'award,year\nExample,2026\n')

    def test_fetch_explicitly_uses_one_header_row(self):
        root = Path(__file__).resolve().parents[1]
        for name in ('generate_cv', 'sync_spreadsheet'):
            spec = importlib.util.spec_from_file_location(name, root / 'scripts' / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            with tempfile.TemporaryDirectory() as directory:
                module.CACHE_DIR = Path(directory)
                payload = b'title,authors,arxiv,url,date,abstract,type\nA,B,2601.12345,https://arxiv.org/abs/2601.12345,2026,,Preprint\n'
                seen = []
                def fake_open(request, **kwargs):
                    seen.append(request.full_url)
                    return io.BytesIO(payload)
                with patch('urllib.request.urlopen', side_effect=fake_open), patch('sys.argv', ['test']):
                    records = module.fetch_tab('publications')
                self.assertEqual(records[0]['title'], 'A')
                query = parse_qs(urlparse(seen[0]).query)
                self.assertEqual(query['format'], ['csv'])
                self.assertTrue(urlparse(seen[0]).path.endswith('/export'))

class ClassificationTests(unittest.TestCase):
    def test_panels_courses_and_expository_are_separate(self):
        rows = [{'title': 'Research', 'event': 'A', 'date': '2020-01-01', 'block': 'Research'},
                {'title': 'Panel', 'event': 'B', 'date': '2020-01-01', 'block': 'Panels'},
                {'title': 'Course', 'event': 'C', 'date': '2020-01-01', 'block': 'Minicourse'},
                {'title': 'Exposition', 'event': 'D', 'date': '2020-01-01', 'block': 'Expository'},
                {'title': 'Future course', 'event': 'E', 'date': '2999-01-01', 'block': 'Short Courses and Workshops'}]
        text = cv.gen_talks(rows)
        self.assertLess(text.index('Short Courses and Workshops'), text.index('Course}'))
        self.assertLess(text.index('Panels}'), text.index('Panel}'))
        self.assertNotIn('Future course', text)
        self.assertIn('Talks are grouped by topic', text)

    def test_empty_canceled_travel_rows_do_not_render(self):
        result = cv.gen_travel([{'title': '', 'location': '', 'date': '', 'date_end': ''}])
        self.assertNotIn('\\cventry', result)

    def test_awards_heading_includes_undergraduate_awards(self):
        self.assertNotIn('Postgraduate', cv.gen_awards([]))

    def test_month_only_dates_do_not_invent_a_day(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('sync', root / 'scripts' / 'sync_spreadsheet.py')
        sync = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sync)
        self.assertEqual(sync.format_event_date(sync.parse_date('2026-06'), '2026-06'), 'Jun 2026')
        self.assertEqual(sync.format_event_date(sync.parse_date('2026-10'), '2026-10'), 'Oct 2026')
        self.assertEqual(sync.format_event_date(sync.parse_date('2026-06-14'), '2026-06-14'), 'Jun 14, 2026')
        with tempfile.TemporaryDirectory() as directory:
            sync.PROJECT_DIR = Path(directory)
            (sync.PROJECT_DIR / 'content' / 'talks').mkdir(parents=True)
            sync.gen_talks_page([{'title': 'Macau', 'event': 'University of Macau', 'date': '2026-06'},
                                 {'title': 'Aspen', 'event': 'Aspen', 'date': '2026-10'}])
            output = (sync.PROJECT_DIR / 'content' / 'talks' / '_index.md').read_text()
            self.assertIn('Jun 2026', output)
            self.assertIn('Oct 2026', output)
            self.assertNotIn('Jun 01', output)
            self.assertNotIn('Oct 01', output)

if __name__ == '__main__':
    unittest.main()
