#!/usr/bin/env python3
"""Exercise investigation control, portability, and recovery with synthetic engineering input."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from smoke import start,stop,request,wait_for


def utility(app,root,script,*arguments):
    payload=app/'payload'
    env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1',
         'PYTHONPATH':os.pathsep.join([str(payload/'api-packages'),str(payload/'components/backend/src')]),'LD_LIBRARY_PATH':str(payload/'postgres/lib')}
    result=subprocess.run([str(payload/'python/bin/python3.12'),'-s',str(app/script),'--payload',str(payload),'--workspace',str(root),*arguments],env=env,capture_output=True,text=True,timeout=300)
    if result.returncode:raise RuntimeError(script+': '+result.stdout[-2500:]+result.stderr[-2500:])
    return json.loads(result.stdout.strip().splitlines()[-1])


def exercise(app,directory):
    if directory.exists():raise ValueError('The product check needs a new output directory.')
    directory.mkdir(parents=True);processes=[];report={'scope':'Engineering checks with synthetic input. No model calls or scientific validation.','checks':{}}
    try:
        first=directory/'first';second=directory/'second';restored=directory/'restored'
        process,ready=start(app,first,True);processes.append((process,first));base=ready['api_url'];token=(first/'owner.token').read_text().strip()
        env={'PATH':'/usr/bin:/bin','PYTHONPATH':str(app/'payload/worker-packages'),'PYTHONDONTWRITEBYTECODE':'1','HOME':str(first/'home')}
        subprocess.run([str(app/'payload/python/bin/python3.12'),'-s',str(app/'checks/fixture.py'),str(first/'raw/tess-spoc-light-curves')],env=env,check=True)
        request(base,'/api/datasets/tess-spoc-light-curves/index',token,method='POST',expected=202)
        observations=wait_for(lambda:request(base,'/api/observations?state=ready',token)['items']);oid=observations[0]['id']
        method=request(base,'/api/investigations/schema',token)['method']
        plan={'contract':'investigation-plan/1','title':'Synthetic product check','question':'Does the desktop preserve and reproduce an engineering result?',
              'purpose':'exploratory','method':{'id':'tess-bls','version':1},'parameters':method['defaults'],'observation_ids':[oid],'exclusions':[],
              'limits':{'download_bytes':134217728,'files':1,'jobs':4,'compute_seconds':2400,'model_turns':2,'model_tokens':1000},
              'stop_conditions':'Stop after the engineering check. This is not a scientific evaluation.','blinding':'open'}
        investigation=request(base,'/api/investigations',token,body=plan,expected=201);cid=investigation['id']
        def approve(inv):
            revision=next(r for r in inv['revisions'] if r['id']==inv['head_revision_id'])
            return request(base,'/api/investigations/'+cid+'/approve',token,body={'revision_id':revision['id'],'sha256':revision['sha256']})
        approve(investigation)
        execute={'revision_id':investigation['head_revision_id'],'request_key':'engineering-repeatable'}
        run_id=request(base,'/api/investigations/'+cid+'/execute',token,body=execute,expected=201)['run_id']
        assert request(base,'/api/investigations/'+cid+'/execute',token,body=execute,expected=201)['run_id']==run_id
        def finished(url,credential,rid):
            result=request(url,'/api/runs/'+rid,credential)
            if all(j['state'] not in ('queued','running') for j in result['jobs']):
                assert all(j['state']=='complete' for j in result['jobs']),result
                return result
        wait_for(lambda:finished(base,token,run_id))
        report['checks']['approved_plan_and_idempotent_execution']=True
        with zipfile.ZipFile(io.BytesIO(request(base,'/api/runs/'+run_id+'/export?artifacts=all',token,raw=True))) as archive:
            measurements=json.loads(archive.read('measurements.json'));saved=json.loads(archive.read('investigation.json'))
            assert saved['approvals'] and saved['events']
        candidate=request(base,'/api/candidates',token,body={'contract':'candidate/1','kind':'transit_signal','tier':'platform',
            'summary':'Synthetic engineering evidence. No astronomical interpretation.','observation_ids':[oid],
            'evidence':[{'kind':'measurement','id':measurements[0]['measurement_id']}]},expected=201)
        request(base,'/api/assessments',token,body={'contract':'assessment/1','candidate_id':candidate['id'],'axis':'evidence','status':'unreviewed','basis':'review','reason':'This synthetic fixture checks application behavior.'},expected=201)
        report['checks']['candidate_and_review_record']=True
        changed=json.loads(json.dumps(plan));changed['parameters']['search']['oversample']+=1
        request(base,'/api/investigations/'+cid+'/revisions',token,body={'document':changed,'parent_id':investigation['head_revision_id'],'expected_head_id':investigation['head_revision_id']},expected=201)
        branch=request(base,'/api/investigations/'+cid,token);approve(branch)
        branch_run=request(base,'/api/investigations/'+cid+'/execute',token,body={'revision_id':branch['head_revision_id'],'request_key':'engineering-branch'},expected=201)['run_id']
        wait_for(lambda:finished(base,token,branch_run))
        compared=request(base,f'/api/runs/compare?run_a={run_id}&run_b={branch_run}',token)
        assert compared
        report['checks']['preserved_branch_and_comparison']=True
        package=directory/'reproduction.zip';utility(app,first,'reproduction.py','export','--run-id',run_id,'--path',str(package),'--include-inputs')
        process2,ready2=start(app,second,True);processes.append((process2,second));base2=ready2['api_url'];token2=(second/'owner.token').read_text().strip()
        imported=utility(app,second,'reproduction.py','import','--path',str(package))
        wait_for(lambda:request(base2,'/api/observations?state=ready',token2)['items'])
        prepared=utility(app,second,'reproduction.py','prepare','--id',imported['id']);repeat_cid=prepared['campaign_id']
        assert utility(app,second,'reproduction.py','prepare','--id',imported['id'])['campaign_id']==repeat_cid
        repeat=request(base2,'/api/investigations/'+repeat_cid,token2);head=repeat['revisions'][0]
        request(base2,'/api/investigations/'+repeat_cid+'/approve',token2,body={'revision_id':head['id'],'sha256':head['sha256']})
        repeat_run=request(base2,'/api/investigations/'+repeat_cid+'/execute',token2,body={'revision_id':head['id'],'request_key':'engineering-portable-repeat'},expected=201)['run_id']
        wait_for(lambda:finished(base2,token2,repeat_run))
        result=utility(app,second,'reproduction.py','compare','--id',imported['id'],'--run-id',repeat_run)
        assert result['status']=='matched' and result['runtime_match'] and result['compared']>0,result
        report['reproduction']=result;report['checks']['numerical_repeat_in_second_empty_workspace']=True
        utility(app,second,'reproduction.py','import','--path',str(package));wait_for(lambda:request(base2,'/api/observations',token2)['total']==1)
        report['checks']['repeat_import_preserves_observation_identity']=True
        backup=directory/'backup.zip';utility(app,first,'recovery.py','backup','--path',str(backup))
        utility(app,first,'recovery.py','restore','--path',str(backup),'--destination',str(restored))
        process3,ready3=start(app,restored,True);processes.append((process3,restored));token3=(restored/'owner.token').read_text().strip()
        assert token3!=token
        request(ready3['api_url'],'/api/me',token,expected=401)
        preserved=request(ready3['api_url'],'/api/investigations/'+cid,token3)
        assert preserved['approved_revision_id']==branch['head_revision_id'] and len(preserved['executions'])==2
        assert request(ready3['api_url'],'/api/runs/'+run_id,token3)['jobs'][0]['state']=='complete'
        assert request(ready3['api_url'],'/api/candidates/'+candidate['id'],token3)['id']==candidate['id']
        report['checks']['backup_restore_records_results_and_rotated_credentials']=True
        assert request(base,'/api/health')['status']=='ok'
        report['checks']['restore_preserves_original_running_workspace']=True
        stop(process,first);processes.remove((process,first))
        restarted,state=start(app,first,True);processes.append((restarted,first))
        assert request(state['api_url'],'/api/investigations/'+cid,token)['approved_revision_id']==branch['head_revision_id']
        report['checks']['restart_preserves_approved_branch']=True
        report['status']='passed'
    except Exception as error:report.update(status='failed',error=str(error));raise
    finally:
        for process,root in reversed(processes):
            try:stop(process,root)
            except Exception as error:report.update(status='failed',shutdown_error=str(error))
        (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--app',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();exercise(args.app.resolve(),args.output.resolve())
