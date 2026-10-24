"""Portable evidence packages. Scientific execution always uses the local API and worker."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path,PurePosixPath
import shutil
import stat
import tempfile
import urllib.request
import uuid
import zipfile
from storage import check as check_storage

MAX_BYTES=3*1024**3
MAX_EVIDENCE=512*1024**2
MAX_MEMBERS=10000
RESERVE=512*1024**2


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def json_bytes(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def validate(payload,name,value):
    from jsonschema import Draft202012Validator,FormatChecker
    path=payload/'components/backend/vendor/contracts'/name
    Draft202012Validator(json.loads(path.read_text()),format_checker=FormatChecker()).validate(value)
    return value


def comparison(payload):
    schema=json.loads((payload/'components/backend/vendor/contracts/records/reproduction-package/v1.schema.json').read_text())
    return {key:value['const'] for key,value in schema['properties']['comparison']['properties'].items()}


def safe_members(archive):
    names=set();size=0
    for item in archive.infolist():
        name=item.filename;path=PurePosixPath(name)
        if (not name or name.startswith('/') or '\\' in name or '\x00' in name or '..' in path.parts
            or str(path)!=name or item.is_dir() or stat.S_ISLNK(item.external_attr>>16) or name in names):
            raise ValueError('The package contains an unsafe or repeated path.')
        names.add(name);size+=item.file_size
        if size>MAX_BYTES or len(names)>MAX_MEMBERS:raise ValueError('The package exceeds the extraction limit.')
    return names,size


def bounded_read(archive,name,limit):
    if archive.getinfo(name).file_size>limit:raise ValueError('A package document exceeds its size limit.')
    return archive.read(name)


def checked_evidence(payload,data):
    if len(data)>MAX_EVIDENCE:raise ValueError('The evidence export exceeds 512 MiB.')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names,_=safe_members(archive)
        manifest=json.loads(bounded_read(archive,'manifest.json',8*1024**2))
        validate(payload,'exports/manifest/v1.schema.json',manifest)
        expected={'manifest.json'}|{item['path'] for item in manifest['files']}
        if len(manifest['files'])!=len(expected)-1 or names!=expected:raise ValueError('The evidence file list does not match its manifest.')
        if manifest['subject']['kind']!='run' or manifest['withheld'] or manifest['protected_excluded']:
            raise ValueError('Reproduction needs an unrestricted run export from a person.')
        for item in manifest['files']:
            with archive.open(item['path']) as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            if archive.getinfo(item['path']).file_size!=item['bytes'] or sha!=item['sha256']:
                raise ValueError('An evidence file failed its integrity check.')
        result={name:json.loads(bounded_read(archive,name,64*1024**2)) for name in ('run.json','observations.json','measurements.json')}
        result['manifest']=manifest
        return result


def request(root,path,body=None,raw=False):
    runtime=json.loads((root/'runtime.json').read_text());token=(root/'owner.token').read_text().strip()
    req=urllib.request.Request(runtime['api_url']+'/api'+path,data=None if body is None else json_bytes(body),
        headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method='GET' if body is None else 'POST')
    with urllib.request.urlopen(req,timeout=120) as response:
        data=response.read(MAX_EVIDENCE+1)
    if len(data)>MAX_EVIDENCE:raise ValueError('The API response exceeds the evidence limit.')
    return data if raw else json.loads(data)


def ensure_root(root):
    if root!=root.resolve() or root.is_symlink():raise ValueError('The workspace must not contain symbolic links.')
    if json.loads((root/'workspace.json').read_text()).get('kind')!='delta-desktop-prototype/1':raise ValueError('Select a Delta desktop workspace.')


def raw_path(root,item):
    parent=root/'raw'/item['dataset_id'];path=parent/item['relative_path']
    if parent.is_symlink() or path.is_symlink() or path.resolve().parent!=parent.resolve():raise ValueError('An observation path is unsafe.')
    return path


def export_package(payload,root,run_id,destination,include_inputs):
    uuid.UUID(run_id);ensure_root(root)
    evidence=request(root,f'/runs/{run_id}/export?artifacts=all',raw=True)
    source=checked_evidence(payload,evidence)
    if not source['run.json']['jobs'] or any(j['state']!='complete' for j in source['run.json']['jobs']):
        raise ValueError('Reproduction needs a completed run.')
    inputs=[]
    for observation in source['observations.json']:
        item={key:observation[key] for key in ('dataset_id','relative_path','bytes','sha256')}
        item.update(observation_id=observation['id'],included=include_inputs,source_uri=observation.get('provenance',{}).get('source_uri'))
        inputs.append(item)
    document={'contract':'reproduction-package/1','run_id':run_id,'evidence':{'path':'evidence.zip','bytes':len(evidence),'sha256':hashlib.sha256(evidence).hexdigest()},'inputs':inputs,'comparison':comparison(payload)}
    validate(payload,'records/reproduction-package/v1.schema.json',document)
    total=len(evidence)+sum(i['bytes'] for i in inputs if i['included'])
    if total>MAX_BYTES or shutil.disk_usage(destination.parent).free<total+RESERVE:raise ValueError('The export exceeds available storage or the package limit.')
    if destination.exists():raise ValueError('Choose a new package filename. Existing files are preserved.')
    fd,temp=tempfile.mkstemp(prefix='.delta-export-',dir=destination.parent);os.close(fd);temporary=Path(temp)
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive:
            archive.writestr('reproduction.json',json_bytes(document));archive.writestr('evidence.zip',evidence)
            for item in inputs:
                if not item['included']:continue
                path=raw_path(root,item)
                if not path.is_file() or path.stat().st_size!=item['bytes'] or digest(path)!=item['sha256']:raise ValueError('An original observation is missing or changed.')
                archive.write(path,'raw/'+item['dataset_id']+'/'+item['relative_path'])
        # Verify streamed inputs again before making the package visible.
        inspect_package(payload,temporary)
        os.link(temporary,destination)
    finally:temporary.unlink(missing_ok=True)
    return {'path':str(destination),'inputs':len(inputs),'includes_observations':include_inputs}


def inspect_package(payload,path):
    with zipfile.ZipFile(path) as archive:
        names,total=safe_members(archive)
        document=json.loads(bounded_read(archive,'reproduction.json',1024**2))
        validate(payload,'records/reproduction-package/v1.schema.json',document)
        expected={'reproduction.json','evidence.zip'}|{'raw/'+i['dataset_id']+'/'+i['relative_path'] for i in document['inputs'] if i['included']}
        if names!=expected or len({i['observation_id'] for i in document['inputs']})!=len(document['inputs']):raise ValueError('The package input list is inconsistent.')
        evidence=bounded_read(archive,'evidence.zip',MAX_EVIDENCE)
        if len(evidence)!=document['evidence']['bytes'] or hashlib.sha256(evidence).hexdigest()!=document['evidence']['sha256']:raise ValueError('The evidence archive failed its integrity check.')
        source=checked_evidence(payload,evidence)
        observations={o['id']:o for o in source['observations.json']}
        if source['manifest']['subject']['id']!=document['run_id'] or set(observations)!={i['observation_id'] for i in document['inputs']}:raise ValueError('The source run or inputs do not match the evidence.')
        for item in document['inputs']:
            if any(item[key]!=observations[item['observation_id']][key] for key in ('dataset_id','relative_path','bytes','sha256')):raise ValueError('The package input differs from the exported observation.')
            if item['included']:
                name='raw/'+item['dataset_id']+'/'+item['relative_path']
                with archive.open(name) as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
                if archive.getinfo(name).file_size!=item['bytes'] or sha!=item['sha256']:raise ValueError('An observation failed its integrity check.')
        return document,source,total


def import_package(payload,root,path):
    ensure_root(root);document,source,total=inspect_package(payload,path)
    additional=document['evidence']['bytes']+len(json_bytes(document))+sum(i['bytes'] for i in document['inputs'] if i['included'] and not raw_path(root,i).exists())
    check_storage(payload,root,additional)
    if shutil.disk_usage(root).free<additional+RESERVE:raise ValueError('The workspace needs more free space for this package.')
    parent=root/'reproductions';parent.mkdir(mode=0o700,exist_ok=True)
    if parent.is_symlink():raise ValueError('The reproduction directory must not be a symbolic link.')
    ident=str(uuid.uuid4());directory=parent/ident;directory.mkdir(mode=0o700)
    try:
        with zipfile.ZipFile(path) as archive:
            # Check all destination collisions before copying an input.
            for item in document['inputs']:
                target=raw_path(root,item)
                if target.exists() and (not target.is_file() or target.stat().st_size!=item['bytes'] or digest(target)!=item['sha256']):raise ValueError('A different observation already uses this filename.')
            for item in document['inputs']:
                target=raw_path(root,item)
                if not item['included'] or target.exists():continue
                fd,temp=tempfile.mkstemp(prefix='.delta-input-',dir=target.parent);os.close(fd);temporary=Path(temp)
                try:
                    with archive.open('raw/'+item['dataset_id']+'/'+item['relative_path']) as src,temporary.open('wb') as dst:shutil.copyfileobj(src,dst,1024**2)
                    if digest(temporary)!=item['sha256']:raise ValueError('The package changed during import.')
                    os.link(temporary,target)
                finally:temporary.unlink(missing_ok=True)
            (directory/'reproduction.json').write_bytes(json_bytes(document))
            (directory/'evidence.zip').write_bytes(bounded_read(archive,'evidence.zip',MAX_EVIDENCE))
        request(root,'/datasets/tess-spoc-light-curves/index',{})
        return {'id':ident,'run_id':document['run_id'],'inputs':len(document['inputs']),'message':'The worker is indexing the inputs. Prepare the repeat after indexing completes.'}
    except Exception:
        shutil.rmtree(directory);raise


def saved(root,ident):
    uuid.UUID(ident);path=root/'reproductions'/ident
    if path.is_symlink() or path.resolve().parent!=(root/'reproductions').resolve():raise ValueError('Invalid reproduction directory.')
    return path


def prepare_repeat(payload,root,ident):
    directory=saved(root,ident)
    document=validate(payload,'records/reproduction-package/v1.schema.json',json.loads((directory/'reproduction.json').read_text()))
    source=checked_evidence(payload,(directory/'evidence.zip').read_bytes())
    observations=[];offset=0
    while True:
        page=request(root,f'/observations?state=ready&limit=1000&offset={offset}')['items'];observations+=page
        if len(page)<1000:break
        offset+=len(page)
    by_hash={o['sha256']:o for o in observations};missing=[i['relative_path'] for i in document['inputs'] if i['sha256'] not in by_hash]
    if missing:return {'missing':missing,'message':'Import or acquire these exact inputs, then prepare the repeat again.'}
    old=source['run.json']['run'];plan={'contract':'investigation-plan/1','title':'Reproduce '+document['run_id'][:8],
      'question':'Do the recorded inputs and parameters reproduce the exported numerical measurements?',
      'purpose':'exploratory','method':{'id':old['method_id'],'version':old['method_version']},'parameters':old['parameters'],
      'observation_ids':[by_hash[i['sha256']]['id'] for i in document['inputs']],'exclusions':[],
      'limits':{'download_bytes':max(1,sum(i['bytes'] for i in document['inputs'])),'files':len(document['inputs']),'jobs':len(document['inputs']),
                'compute_seconds':600*len(document['inputs']),'model_turns':1,'model_tokens':1000},
      'stop_conditions':'Stop after one repeat and comparison with the preserved evidence. Numerical agreement does not establish scientific validity.','blinding':'open'}
    created=request(root,'/investigations',plan)
    # A repeated prepare operation reuses its draft; the GUI still requires exact approval.
    (directory/'investigation.json').write_bytes(json_bytes({'campaign_id':created['id']}))
    return {'campaign_id':created['id'],'message':'Review and approve the imported plan in Investigations. Run it once, then compare its result.'}


def compare_measurements(original,repeated,limits):
    def mapping(source):
        observations={o['id']:o['sha256'] for o in source['observations.json']};out={}
        for item in source['measurements.json']:
            if item['role']=='reference_comparison':continue
            key='|'.join([observations[item['observation_id']],item['role'],item['name'],item['unit']])
            if key in out:raise ValueError('The evidence contains repeated measurement keys.')
            out[key]=item
        return out
    a,b=mapping(original),mapping(repeated);differences=[]
    for key in sorted(set(a)|set(b)):
        if key not in a or key not in b:differences.append({'key':key,'reason':'The measurement is missing from one run.'});continue
        x,y=a[key]['value'],b[key]['value']
        equal=(type(x) is type(y) and x==y) if isinstance(x,bool) or isinstance(y,bool) or x is None or y is None else math.isclose(x,y,abs_tol=limits['absolute'],rel_tol=limits['relative'])
        if not equal:differences.append({'key':key,'reason':f'The numerical values differ: {x!r} versus {y!r}.'})
        for field in ('uncertainty','quality_flags','time_scale','time_reference'):
            if a[key].get(field)!=b[key].get(field):differences.append({'key':key,'reason':'The measurement metadata differs: '+field+'.'})
    return len(set(a)&set(b)),differences


def compare_repeat(payload,root,ident,run_id):
    uuid.UUID(run_id);directory=saved(root,ident)
    document=json.loads((directory/'reproduction.json').read_text());original=checked_evidence(payload,(directory/'evidence.zip').read_bytes())
    if run_id==document['run_id']:raise ValueError('Select a new repeat run. The source run cannot verify itself.')
    link=json.loads((directory/'investigation.json').read_text())
    investigation=request(root,'/investigations/'+link['campaign_id'])
    if run_id not in {e['run_id'] for e in investigation['executions']}:raise ValueError('Select a run from the prepared repeat investigation.')
    repeated=checked_evidence(payload,request(root,f'/runs/{run_id}/export?artifacts=all',raw=True))
    count,differences=compare_measurements(original,repeated,document['comparison'])
    old,new=original['run.json'],repeated['run.json'];complete=bool(new['jobs']) and all(j['state']=='complete' for j in new['jobs'])
    for field in ('method_id','method_version','parameters'):
        if old['run'][field]!=new['run'][field]:differences.append({'key':field,'reason':'The method or parameters differ.'})
    if {o['sha256'] for o in original['observations.json']}!={o['sha256'] for o in repeated['observations.json']}:differences.append({'key':'inputs','reason':'The input checksums differ.'})
    software=lambda source: sorted(json.dumps(j.get('result',{}).get('software'),sort_keys=True) for j in source['jobs'] if j.get('result'))
    runtime_match=software(old)==software(new)
    report={'contract':'reproduction-report/1','source_run_id':document['run_id'],'repeat_run_id':run_id,
            'status':'unavailable' if not complete or not count else 'different' if differences else 'matched','runtime_match':runtime_match,
            'comparison':document['comparison'],'compared':count,'differences':differences,
            'notes':['Reference-label comparisons are excluded. The report compares worker measurements, units, metadata, and exact input hashes.']+([] if runtime_match else ['The recorded runtime versions differ. Numerical agreement does not establish runtime equivalence.'])}
    validate(payload,'records/reproduction-report/v1.schema.json',report)
    path=directory/('report-'+str(uuid.uuid4())+'.json');path.write_bytes(json_bytes(report))
    return {**report,'path':str(path)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,required=True);parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('action',choices=['export','import','prepare','compare','list']);parser.add_argument('--path',type=Path);parser.add_argument('--run-id');parser.add_argument('--id');parser.add_argument('--include-inputs',action='store_true')
    args=parser.parse_args();payload=args.payload.resolve();root=args.workspace.absolute()
    if args.action=='export':result=export_package(payload,root,args.run_id,args.path,args.include_inputs)
    elif args.action=='import':result=import_package(payload,root,args.path)
    elif args.action=='prepare':
        path=saved(root,args.id)/'investigation.json'
        result=json.loads(path.read_text()) if path.exists() else prepare_repeat(payload,root,args.id)
    elif args.action=='compare':result=compare_repeat(payload,root,args.id,args.run_id)
    else:result={'items':[{'id':p.parent.name,**json.loads(p.read_text())} for p in sorted((root/'reproductions').glob('*/reproduction.json'))]}
    print(json.dumps(result))

if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'error':str(error)}));raise SystemExit(1)
