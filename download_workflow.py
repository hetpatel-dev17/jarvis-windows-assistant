"""Bounded public PDF/ZIP retrieval. No installation, extraction, or execution."""
import hashlib
import json
import os
import ssl
import time
import uuid
from pathlib import Path
from urllib.parse import urljoin

import httpx


class Downloads:
    def __init__(self, root, limit=50*1024*1024):
        self.root = Path(root)
        self.limit = limit

    def control(self, action, url='', kind='pdf', check_url=lambda u:u,
                cancelled=lambda:False, seconds=90):
        if action != 'download' or kind not in ('pdf', 'zip'):
            raise ValueError('Download supports a public PDF or ZIP link only.')
        check_url(url)
        self.root.mkdir(parents=True, exist_ok=True)
        identity = hashlib.sha256((kind+'\n'+url).encode()).hexdigest()
        folder = self.root / identity
        folder.mkdir(exist_ok=True)
        record = folder / 'receipt.json'
        destination = folder / ('download.'+kind)
        if record.exists() and destination.exists():
            receipt = json.loads(record.read_text(encoding='utf-8'))
            if hashlib.sha256(destination.read_bytes()).hexdigest() == receipt['sha256']:
                return dict(status='already_saved', path=str(destination), message='This file is already saved and checked.')
        deadline = time.monotonic() + seconds
        attempts = 0
        def guard():
            if cancelled():
                raise RuntimeError('Stopped by you.')
            if time.monotonic() >= deadline:
                raise TimeoutError('Download time limit reached. No completed file was reported.')
        for attempt in range(3):
            guard()
            attempts += 1
            temporary = folder / (uuid.uuid4().hex+'.part')
            try:
                current = url
                # No browser cookies, provider keys, or credentials are forwarded.
                tls = ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE'))
                with httpx.Client(follow_redirects=False, trust_env=False, verify=tls) as client:
                    for redirect in range(6):
                        guard()
                        check_url(current)
                        with client.stream('GET', current, timeout=min(10, max(.1, deadline-time.monotonic()))) as response:
                            if response.status_code in (301,302,303,307,308):
                                current = urljoin(current, response.headers['location'])
                                check_url(current)
                                continue
                            response.raise_for_status()
                            if int(response.headers.get('content-length', '0')) > self.limit:
                                raise ValueError('This file exceeds the 50 MB download limit.')
                            size = 0
                            with temporary.open('xb') as output:
                                for chunk in response.iter_bytes(65536):
                                    guard()
                                    size += len(chunk)
                                    if size > self.limit:
                                        raise ValueError('This file exceeds the download size limit.')
                                    output.write(chunk)
                            break
                    else:
                        raise ValueError('Too many redirects. Download stopped.')
                guard()
                with temporary.open('rb') as source:
                    magic = source.read(8)
                if not (magic.startswith(b'%PDF-') if kind == 'pdf' else magic.startswith((b'PK\x03\x04', b'PK\x05\x06'))):
                    raise ValueError('The website returned a different file or a sign-in page. Nothing was saved as complete.')
                digest = hashlib.sha256(temporary.read_bytes()).hexdigest()
                os.replace(temporary, destination)
                receipt = dict(sha256=digest, bytes=size, attempts=attempts, kind=kind)
                pending = folder / 'receipt.tmp'
                pending.write_text(json.dumps(receipt), encoding='utf-8')
                os.replace(pending, record)
                return dict(status='saved', path=str(destination), **receipt,
                            message='Downloaded and checked the file. It was not opened or installed.')
            except (httpx.TransportError, httpx.HTTPStatusError) as error:
                if isinstance(error, httpx.HTTPStatusError) and error.response.status_code not in (408,429,500,502,503,504):
                    raise
                if attempt == 2:
                    raise RuntimeError('The connection failed after three attempts. No completed file was reported.') from error
                for _ in range(4*(attempt+1)):
                    guard()
                    time.sleep(.25)
            finally:
                temporary.unlink(missing_ok=True)
