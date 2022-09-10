import os
import re
import json
import shutil
import subprocess as sp
import time
from typing import List
import logger

target_pattern = r'^(\w+): cmake_check_build_system'


def scan_headers(item):
    cmd = item.get('command').split()
    try:
        i = cmd.index('-o')
        del cmd[i:i + 2]
    except ValueError:
        pass
    cmd.insert(1, '-MM')
    cp = sp.run(cmd, capture_output=True, cwd=item.get('directory'))
    headers = []
    for line in cp.stdout.decode('utf-8').split():
        if line.endswith('.h'):
            headers.append(line)
    return headers


def paths2tree(source_root: str, file_paths: List[str]):
    root = {}
    for path in sorted(file_paths):
        rel = os.path.relpath(path, source_root)
        parts = []
        while rel:
            head, tail = os.path.split(rel)
            parts.append(tail)
            rel = head
        parts = list(reversed(parts))
        # logger.logwrite(str(parts))
        cur = root
        for part in parts[0:-1]:
            if part not in cur:
                cur[part] = {}
            cur = cur.get(part)
        cur[parts[-1]] = ''
    return root


def scan_cmake(build_folder: str, makefile_path: str):
    source_root = ''
    targets = []
    logger.logwrite(f'Reading makefile: "{makefile_path}"')
    start = time.time()
    for line in open(makefile_path).readlines():
        if line.startswith('CMAKE_SOURCE_DIR'):
            source_root = line.split()[-1]
            logger.logwrite(f'Setting source_root to "{source_root}"  {time.time() - start}s')
            break
    start = time.time()
    for line in open(makefile_path).readlines():
        m = re.match(target_pattern, line)
        if m:
            target = m.groups()[0]
            logger.logwrite(f'target="{target}"')
            targets.append(target)
    logger.logwrite(f'Found all targets. {time.time() - start}s')
    if not source_root:
        raise RuntimeError('No source root in makefile')
    commands_path = os.path.join(build_folder, 'compile_commands.json')
    if not os.path.exists(commands_path):
        raise RuntimeError('compile_commands.json not found')
    shutil.copy(commands_path, source_root)
    start = time.time()
    compile_commands = json.load(open(commands_path))
    logger.logwrite(f'Loaded compile commands. {time.time() - start}s')
    file_paths = set()
    start = time.time()
    for item in compile_commands:
        filename = item.get('file')
        # logger.logwrite(f'Adding source: {filename}')
        file_paths.add(filename)
        headers = scan_headers(item)
        # logger.logwrite(f'Headers:\n{headers}\n------------------------')
        for header in headers:
            file_paths.add(header)
    logger.logwrite(f'Scanned headers. {time.time() - start}s')
    return source_root, paths2tree(source_root, list(file_paths)), targets
