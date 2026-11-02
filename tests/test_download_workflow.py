import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from download_workflow import Downloads


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counts = {}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                cls.counts[self.path] = cls.counts.get(self.path, 0)+1
                if self.path == '/redirect':
                    self.send_response(302); self.send_header('Location', '/pdf'); self.end_headers(); return
                if self.path == '/badredirect':
                    self.send_response(302); self.send_header('Location', 'http://blocked.invalid/file'); self.end_headers(); return
                if self.path == '/temporary' and cls.counts[self.path] == 1:
                    self.send_response(503); self.end_headers(); return
                payload = b'<html>Sign in</html>' if self.path == '/login' else b'%PDF-1.4\nfixture\n%%EOF'
                self.send_response(200); self.send_header('Content-Length', str(len(payload))); self.end_headers(); self.wfile.write(payload)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.base = 'http://127.0.0.1:'+str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def test_redirect_save_repeat_and_corruption(self):
        with tempfile.TemporaryDirectory() as root:
            service = Downloads(root)
            result = service.control('download', self.base+'/redirect')
            self.assertEqual(result['status'], 'saved')
            count = self.counts['/pdf']
            self.assertEqual(service.control('download', self.base+'/redirect')['status'], 'already_saved')
            self.assertEqual(self.counts['/pdf'], count)
            Path(result['path']).write_bytes(b'corrupt')
            self.assertEqual(service.control('download', self.base+'/redirect')['status'], 'saved')

    def test_temporary_failure_retries(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(Downloads(root).control('download', self.base+'/temporary')['attempts'], 2)

    def test_html_size_cancel_and_redirect_policy(self):
        with tempfile.TemporaryDirectory() as root:
            service = Downloads(root)
            with self.assertRaises(ValueError): service.control('download', self.base+'/login')
            with self.assertRaises(ValueError): Downloads(root, limit=5).control('download', self.base+'/pdf')
            with self.assertRaises(RuntimeError): service.control('download', self.base+'/pdf', cancelled=lambda:True)
            def validate(url):
                if 'blocked.invalid' in url: raise ValueError('blocked')
                return url
            with self.assertRaises(ValueError): service.control('download', self.base+'/badredirect', check_url=validate)
            self.assertFalse(list(Path(root).rglob('*.part')))
            self.assertFalse(list(Path(root).rglob('receipt.json')))
