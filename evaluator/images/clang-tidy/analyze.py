#!/usr/bin/env python3
import os
import subprocess
from collections import defaultdict
import yaml
import json

class OffsetToLine:
    def __init__(self, root):
        self.root = root
        self.files = {}

    def to_line(self, path, offset):
        if path not in self.files:
            self.files[path] = self.build(path)

        for line, threshold in enumerate(self.files[path]):
            if threshold > offset:
                return line + 1
        return len(self.files[path])

    def build(self, path):
        offsets = []
        with open(os.path.join(self.root, path), "rb") as f:
            for offset, byte in enumerate(f.read()):
                if byte == ord('\n'):
                    offsets.append(offset)
        return offsets

cmd = [
    'clang-tidy',
    f"--export-fixes=/tmp/fixes.yaml",
]

s = os.environ.get('PIPE_CHECKS', '')
if s:
    checks = json.loads(s)
    print(f"Checks: {s}")

    cmd.append(f"--checks={','.join(checks)}")

cmd += [os.path.basename(f) for f in os.listdir() if f.endswith(".c") or f.endswith(".cpp")]

print(cmd)
subprocess.Popen(cmd).wait()

offset_to_line = OffsetToLine('')
comments = defaultdict(list)
with open("/tmp/fixes.yaml") as f:
    for err in yaml.load(f.read(), Loader=yaml.SafeLoader)['Diagnostics']:
        seen = set()

        for note in [err, err['DiagnosticMessage'] if 'DiagnosticMessage' in err else {}]: #, *err['Notes']]:
            if 'Message' not in note or note['Message'] in seen:
                continue
            seen.add(note['Message'])
            source = os.path.basename(note['FilePath'])
            comments[source].append({
                'line': offset_to_line.to_line(source, note['FileOffset']),
                'text': note['Message'],
                'source': err['DiagnosticName'],
            })
        
with open('piperesult.json', 'w') as out:
    json.dump({"comments": comments}, out, indent=4, sort_keys=True)
