#!/usr/bin/env python3
"""Stage only tracked public files, excluding repository/operations source roots."""
import os, subprocess, sys, json
from pathlib import Path
import shutil
src, dest = map(lambda x: Path(x).resolve(), sys.argv[1:3])
if src == dest or dest.is_relative_to(src) or dest.exists():
    raise SystemExit("Destination must be a new directory outside source")
exclude_roots={'.github','docs','tests','tools'}
exclude_files={'.gitignore','AGENTS.md','CLAUDE.md'}
private_source={'.gs','.cjs','.py','.yml','.yaml'}
files = [os.fsdecode(p) for p in subprocess.check_output(['git','-C',str(src),'ls-files','-z']).split(b'\0') if p]
dest.mkdir(parents=True)
dest.chmod(0o755)
kept=set()
for name in files:
    if name.split('/')[0] in exclude_roots or name in exclude_files: continue
    # Existing social posts may link to their associated images.
    if name.startswith('sns/') and name != 'sns/illust.svg':
        if not (name.startswith('sns/img/') and Path(name).suffix.lower() in {'.png','.jpg','.jpeg','.webp','.svg','.gif','.avif'}):
            continue
    if Path(name).suffix.lower() in private_source: continue
    src_file=src/name
    if src_file.is_symlink() or not src_file.is_file(): raise SystemExit("Unsupported public file type: "+name)
    target=dest/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src_file,target)
    target.chmod(0o644)
    for directory in target.parents:
        if directory == dest: break
        directory.chmod(0o755)
    kept.add(name)
must={'index.html','404.html','app.js','CNAME','robots.txt','sitemap.xml','sitemap_index.xml',
      'booking/accept-preview.html','.nojekyll','llms.txt','webmcp.js','webmcp/data.json',
      'hospital/data/chiba.json','place-data.json','dog-trainer/kyoto/index.html'}
if must - kept:
    raise SystemExit("Required public files missing: "+", ".join(sorted(must-kept)))
if any((dest/root).exists() for root in exclude_roots):
    raise SystemExit("Internal directories reached website artifact")
if any(Path(name).suffix.lower() in private_source for name in kept):
    raise SystemExit("Internal source type reached website artifact")
for relative in ('webmcp/data.json','place-data.json','hospital/data/chiba.json'):
    with (dest/relative).open(encoding='utf-8') as entry:
        json.load(entry)
print(f"Staged {len(kept)} tracked public files; no ops/source/test roots included.")
