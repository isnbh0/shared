#!/usr/bin/env python3
"""Refresh private offline Antigravity transcript exports from consistent SQLite snapshots."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import time
import uuid


def signature(path):
    parts = []
    for item in (path, Path(str(path) + '-wal')):
        try:
            stat = item.stat()
            parts.append([stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns])
        except FileNotFoundError:
            parts.append(None)
    return parts


def brain_entries(root, ident):
    directory = root / 'brain' / ident
    if directory.is_symlink():
        raise OSError('session artifact directory is a symlink')
    if not directory.exists():
        return []
    entries = []
    def failed(exc):
        raise exc
    for current, dirs, files in os.walk(directory, followlinks=False, onerror=failed):
        for name in dirs:
            if (Path(current) / name).is_symlink():
                raise OSError('session artifact directory contains a symlink')
        for name in files:
            path = Path(current) / name
            if path.is_symlink() or not path.is_file():
                raise OSError('session artifact is not a regular file')
            st = path.stat()
            entries.append((str(path.relative_to(directory)), st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns))
    return sorted(entries)


def capture_artifacts(root, ident, entries, store):
    result = {}
    for rel, dev, inode, size, mtime in entries:
        path = root / 'brain' / ident / rel
        data = path.read_bytes()
        st = path.stat()
        if (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns) != (dev, inode, size, mtime):
            raise OSError('session artifact changed during capture')
        digest = hashlib.sha256(data).hexdigest()
        target = store / digest
        if target.is_symlink() or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            fd, name = tempfile.mkstemp(prefix='.object-', dir=store)
            try:
                with os.fdopen(fd, 'wb') as out:
                    out.write(data)
                os.replace(name, target)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
        result[rel] = digest
    return result


def atomic_json(path, obj):
    fd, name = tempfile.mkstemp(prefix='.status-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(obj, out, ensure_ascii=False, sort_keys=True, indent=2)
            out.write('\n')
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def sync(root, output, reader, source_reader=None):
    os.umask(0o077)
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    if output.is_symlink():
        raise ValueError('output directory must not be a symlink')
    output.chmod(0o700)
    lock_path = output / '.lock'
    with lock_path.open('a') as lock:
        deadline = time.monotonic() + 30
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    return 1
                time.sleep(0.2)
        status_path = output / 'status.json'
        try:
            previous = json.loads(status_path.read_text(encoding='utf-8'))
            if previous.get('version') != 1:
                previous = {}
        except (FileNotFoundError, ValueError, OSError):
            previous = {}
        old = previous.get('sessions', {})
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        status = {'version': 1, 'updatedAt': now, 'root': str(root),
                  'reader': str(reader), 'sessions': {}}
        sessions = status['sessions']
        try:
            reader_stat = reader.stat()
            reader_sig = [reader_stat.st_dev, reader_stat.st_ino, reader_stat.st_size, reader_stat.st_mtime_ns]
            if not reader.is_file() or not os.access(reader, os.X_OK):
                raise OSError('reader is not executable')
        except OSError:
            reader_sig = None
            status['error'] = 'reader unavailable; retaining database backups only'
        source_reader_sig = None
        if source_reader is not None:
            try:
                st = source_reader.stat()
                if not source_reader.is_file() or not os.access(source_reader, os.X_OK):
                    raise OSError('source reader is not executable')
                source_reader_sig = [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns]
            except OSError:
                status['sourceReaderError'] = 'source reader unavailable'
        status['sourceReader'] = str(source_reader) if source_reader else None
        conversations = root / 'conversations'
        if not conversations.is_dir():
            status['error'] = 'conversation directory unavailable'
            for key, item in old.items():
                sessions[key] = {**item, 'state': 'stale', 'reason': status['error']}
            atomic_json(status_path, status)
            return 1
        backups = output / 'source'
        backups.mkdir(exist_ok=True, mode=0o700)
        if backups.is_symlink():
            raise ValueError('backup directory must not be a symlink')
        backups.chmod(0o700)
        objects = output / 'artifacts'
        objects.mkdir(exist_ok=True, mode=0o700)
        if objects.is_symlink():
            raise ValueError('artifact directory must not be a symlink')
        objects.chmod(0o700)
        failures = 0
        for source in sorted(conversations.glob('*.db')):
            ident = source.stem
            # Native conversation IDs are UUIDs; avoid treating arbitrary names as paths.
            try:
                if str(uuid.UUID(ident)) != ident.lower():
                    continue
            except ValueError:
                continue
            if source.is_symlink():
                sessions[ident] = {'state': 'stale', 'reason': 'source database is a symlink'}
                failures += 1
                continue
            try:
                brain_before = brain_entries(root, ident)
            except OSError:
                sessions[ident] = {'state': 'stale', 'reason': 'artifact inventory failed; retry next run'}
                failures += 1
                continue
            brain_sig = hashlib.sha256(json.dumps(brain_before, ensure_ascii=False).encode()).hexdigest()
            before = signature(source)
            target = output / (ident + '.json')
            prior = old.get(ident, {})
            if (prior.get('state') in ('ok', 'source_only') and prior.get('signature') == before
                    and prior.get('readerSignature') == reader_sig and prior.get('sourceReaderSignature') == source_reader_sig
                    and prior.get('artifactSignature') == brain_sig
                    and all((objects / h).is_file() and not (objects / h).is_symlink()
                            and hashlib.sha256((objects / h).read_bytes()).hexdigest() == h
                            for h in prior.get('artifacts', {}).values())
                    and target.is_file() and not target.is_symlink()
                    and (backups / (ident + '.db')).is_file() and not (backups / (ident + '.db')).is_symlink()
                    and hashlib.sha256(target.read_bytes()).hexdigest() == prior.get('sha256')
                    and hashlib.sha256((backups / (ident + '.db')).read_bytes()).hexdigest() == prior.get('backupSha256')):
                sessions[ident] = prior
                continue
            item = {'state': 'stale', 'signature': before, 'readerSignature': reader_sig,
                    'sourceReaderSignature': source_reader_sig, 'artifactSignature': brain_sig}
            sessions[ident] = item
            try:
                with tempfile.TemporaryDirectory(prefix='.capture-', dir=output) as temp:
                    db = Path(temp) / (ident + '.db')
                    with contextlib.closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)) as src, contextlib.closing(sqlite3.connect(db)) as dst:
                        src.backup(dst)
                    backup_sha = hashlib.sha256(db.read_bytes()).hexdigest()
                    transcript = Path(temp) / 'export.json'
                    timeout = False
                    if reader_sig is not None:
                        try:
                            proc = subprocess.run([str(reader), 'export-offline', '--format=json', '--out=' + str(transcript), str(db)],
                                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False)
                        except subprocess.TimeoutExpired:
                            proc = None
                            timeout = True
                    else:
                        proc = None
                    changed = signature(source) != before
                    os.chmod(db, 0o600)
                    os.replace(db, backups / (ident + '.db'))
                    item.update(state='stale' if changed else 'raw_only', backupSha256=backup_sha,
                                capturedAt=now)
                    try:
                        captured_artifacts = capture_artifacts(root, ident, brain_before, objects)
                        changed = changed or brain_entries(root, ident) != brain_before
                    except OSError:
                        captured_artifacts = {}
                        changed = True
                    item['artifacts'] = captured_artifacts
                    export_state = 'ok'
                    if proc is None or proc.returncode != 0:
                        reason = ('offline decoder timed out' if timeout else 'reader unavailable') if proc is None else 'offline decoder refused the source'
                        if source_reader_sig is None:
                            item['reason'] = reason
                            failures += 1
                            continue
                        if transcript.exists():
                            transcript.unlink()
                        try:
                            fallback = subprocess.run([str(source_reader), str(backups / (ident + '.db')), str(transcript)],
                                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False)
                        except subprocess.TimeoutExpired:
                            fallback = None
                        if fallback is None or fallback.returncode != 0:
                            item['reason'] = reason + '; source decoder also failed'
                            failures += 1
                            continue
                        export_state = 'source_only'
                    data = transcript.read_bytes()
                    parsed = json.loads(data)
                    offline = parsed.get('agyReader', {}).get('offline', {}) if export_state == 'ok' else parsed.get('sourceRecovery', {})
                    omitted = offline.get('omittedExecutorRecords', 0) if export_state == 'ok' else offline.get('omittedExecutors', 0)
                    if (parsed.get('cascadeId') != ident or not isinstance(parsed.get('steps'), list)
                            or not offline.get('sourceDigest') or omitted):
                        item['reason'] = 'incomplete or invalid offline export'
                        failures += 1
                        continue
                    changed = changed or signature(source) != before
                    os.chmod(transcript, 0o600)
                    os.replace(transcript, target)
                    sessions[ident] = {'state': 'stale' if changed else export_state, 'format': export_state,
                                       'signature': before, 'readerSignature': reader_sig,
                                       'sourceReaderSignature': source_reader_sig,
                                       'sha256': hashlib.sha256(data).hexdigest(), 'backupSha256': backup_sha,
                                       'artifactSignature': brain_sig, 'artifacts': captured_artifacts,
                                       'sourceDigest': offline['sourceDigest'], 'steps': len(parsed['steps']),
                                       'capturedAt': now}
                    if changed:
                        sessions[ident]['reason'] = 'source or artifacts changed during capture; retry next run'
                        failures += 1
            except (OSError, sqlite3.Error, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
                item['reason'] = 'capture failed; retry next run'
                failures += 1
        for ident, prior in old.items():
            if ident not in sessions:
                sessions[ident] = {**prior, 'state': 'missing_source', 'reason': 'source database not present'}
        atomic_json(status_path, status)
        return 1 if failures else 0


def main():
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=home / '.gemini/antigravity-cli')
    parser.add_argument('--output', type=Path, default=home / '.gemini/antigravity-cli/recovery-live')
    parser.add_argument('--reader', type=Path, default=Path(os.environ.get('AGY_READER', '')) if os.environ.get('AGY_READER') else None)
    parser.add_argument('--source-reader', type=Path, default=None)
    args = parser.parse_args()
    reader = args.reader or (Path(shutil.which('agy-reader')) if shutil.which('agy-reader') else None)
    if reader is None:
        reader = args.root.expanduser() / '.agy-reader-unavailable'
    try:
        return sync(args.root.expanduser().resolve(), args.output.expanduser(), reader.expanduser().resolve(),
                    args.source_reader.expanduser().resolve() if args.source_reader else None)
    except (OSError, ValueError) as exc:
        parser.exit(1, 'agy live export: ' + str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
