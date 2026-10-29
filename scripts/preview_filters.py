"""Build the existing frontend into an ignored local folder without changing public/."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build_preview(root=ROOT, output=None, dataset=None):
    root = Path(root)
    output = Path(output) if output is not None else root / 'learning-local/approved-filters-preview'
    # Reuse the existing validated, self-contained builder in an isolated copy.
    with tempfile.TemporaryDirectory(prefix='ke-filter-preview-') as directory:
        isolated = Path(directory)
        shutil.copytree(root / 'web', isolated / 'web')
        (isolated / 'scripts').mkdir()
        for name in ('build_site.py', 'refresh.py'):
            shutil.copy2(root / 'scripts' / name, isolated / 'scripts' / name)
        (isolated / 'public/data').mkdir(parents=True)
        if dataset is None:
            shutil.copy2(root / 'public/data/market.json', isolated / 'public/data/market.json')
        else:
            (isolated / 'public/data/market.json').write_text(
                json.dumps(dataset, ensure_ascii=True), encoding='utf-8')
        subprocess.run([sys.executable, '-B', str(isolated / 'scripts/build_site.py')],
                       check=True, capture_output=True, text=True, encoding='utf-8')
        page = (isolated / 'public/index.html').read_text(encoding='utf-8')
        page = page.replace('<html ', '<html data-local-preview="true" ', 1)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'index.html').write_text(page, encoding='utf-8')
        (output / 'data').mkdir(exist_ok=True)
        shutil.copy2(isolated / 'public/data/market.json', output / 'data/market.json')
    return output.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serve', action='store_true', help='Serve this local preview on loopback only.')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    output = build_preview()
    print(f'Local preview built: {output / "index.html"}', flush=True)
    if args.serve:
        handler = partial(SimpleHTTPRequestHandler, directory=str(output))
        server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
        print(f'Local preview: http://127.0.0.1:{server.server_port}/', flush=True)
        print('No source collection, publication or live data refresh. Ctrl+C stops the server.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
