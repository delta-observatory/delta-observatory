"""Native settings and diagnostic summaries. Credentials and conversation text are excluded."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
from storage import settings,usage
from reproduction import validate
from supervisor import atomic_text


def status(payload,root):
    totals={}
    for folder in ('database','raw','artifacts','reproductions','backups','agent-profiles','logs','cache'):
        totals[folder]=usage(root/folder) if (root/folder).exists() else 0
    return {'workspace':str(root),'storage':settings(payload,root),'used_bytes':usage(root),'free_bytes':shutil.disk_usage(root).free,
            'folders':totals,'sources':json.loads((payload/'sources.json').read_text())['components'],
            'platform':{'system':platform.system(),'release':platform.release(),'machine':platform.machine()},
            'public_exploration':True,'scientific_status':'Exploratory TESS work. Detection completeness, false-alarm rates, and physical planet parameters remain unvalidated.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,required=True);parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('action',choices=['status','save']);parser.add_argument('--reserve-bytes',type=int);parser.add_argument('--maximum-bytes',type=int);args=parser.parse_args()
    if args.action=='save':
        value={'contract':'desktop-storage/1','reserve_bytes':args.reserve_bytes,'maximum_bytes':args.maximum_bytes}
        validate(args.payload,'records/desktop-storage/v1.schema.json',value);atomic_text(args.workspace/'storage.json',json.dumps(value)+'\n')
    print(json.dumps(status(args.payload,args.workspace)))

if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'error':str(error)}));raise SystemExit(1)
