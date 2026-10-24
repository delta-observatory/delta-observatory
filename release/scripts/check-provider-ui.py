"""Check provider screens on an isolated virtual display without network access."""
import argparse
from pathlib import Path
import subprocess
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rootfs',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();root=Path(__file__).resolve().parents[2];output=args.output.resolve()
output.mkdir(parents=True,exist_ok=False);(output/'home').mkdir()
for directory in ('repo','work'):(args.rootfs/directory).mkdir(exist_ok=True)
command=['bwrap','--unshare-all','--die-with-parent','--clearenv','--ro-bind',str(args.rootfs.resolve()),'/',
         '--ro-bind',str(root),'/repo','--bind',str(output),'/work','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--tmpfs','/run',
         '--setenv','PATH','/usr/bin:/bin','--setenv','HOME','/work/home','--setenv','LANG','C.UTF-8','--setenv','DISPLAY',':99',
         '--setenv','DELTA_UI_VIRTUAL_DISPLAY','1','--setenv','DELTA_PROVIDER_UI_PROFILE','/work/profile',
         '--setenv','DELTA_PROVIDER_UI_OUTPUT','/work/check','--chdir','/repo',
         '/bin/sh','-c',
         '/usr/bin/Xvfb :99 -screen 0 1440x1100x24 -nolisten tcp >/work/xvfb.log 2>&1 & '
         'delta_display=$!; trap "kill $delta_display" EXIT; sleep 1; '
         '/repo/release/node_modules/electron/dist/electron /repo/release/tests/provider-ui.cjs']
subprocess.run(command,check=True)
print(output/'check/provider-ui.json')
