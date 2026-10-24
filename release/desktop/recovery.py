"""Data-only desktop backups. Restore never executes SQL supplied by an archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import shutil
import stat
import subprocess
import tempfile
import urllib.parse
import uuid
import zipfile

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from reproduction import digest,json_bytes,validate,ensure_root
from storage import settings,usage
from supervisor import workspace_lock,environment,run_logged,atomic_text

MAX_BACKUP_BYTES=64*1024**3
MAX_FILES=100000


def database_url(root):return 'postgresql://delta@/delta?'+urllib.parse.urlencode({'host':str(root/'socket')})


def tables(conn):
    result=[]
    names=conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename<>'schema_migration' ORDER BY tablename").fetchall()
    for row in names:
        columns=conn.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",[row['tablename']]).fetchall()
        result.append({'name':row['tablename'],'columns':[c['column_name'] for c in columns]})
    return result


def backup(payload,root,destination,include_observations=True):
    ensure_root(root)
    if destination.exists():raise ValueError('Choose a new backup filename. Existing backups are preserved.')
    files=[];policy=settings(payload,root)
    content=[]
    for folder in ['artifacts','reproductions']+(['raw'] if include_observations else []):
        for path in sorted((root/folder).rglob('*')):
            if path.is_symlink():raise ValueError('A backup input contains a symbolic link.')
            if path.is_file() and not path.name.startswith('.') and not path.name.endswith(('.part','.partial','.importing')):content.append(path)
    total=sum(p.stat().st_size for p in content)
    if total>MAX_BACKUP_BYTES or shutil.disk_usage(destination.parent).free<total+policy['reserve_bytes']:raise ValueError('The backup exceeds its 64 GiB limit or available storage.')
    fd,name=tempfile.mkstemp(prefix='.delta-backup-',dir=destination.parent);os.close(fd);temporary=Path(name)
    try:
        with zipfile.ZipFile(temporary,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as archive,psycopg.connect(database_url(root),row_factory=dict_row) as conn:
            conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            table_list=tables(conn)
            migrations=conn.execute('SELECT version,sha256 FROM schema_migration ORDER BY version').fetchall()
            for table in table_list:
                path='database/'+table['name']+'.csv';sha=hashlib.sha256();size=0
                statement=sql.SQL('COPY {} ({}) TO STDOUT WITH (FORMAT CSV)').format(sql.Identifier(table['name']),sql.SQL(',').join(map(sql.Identifier,table['columns'])))
                with archive.open(path,'w',force_zip64=True) as out,conn.cursor().copy(statement) as copy:
                    for block in copy:
                        out.write(block);sha.update(block);size+=len(block)
                files.append({'path':path,'bytes':size,'sha256':sha.hexdigest()})
            content=[]
            for folder in ['artifacts','reproductions']+(['raw'] if include_observations else []):
                for path in sorted((root/folder).rglob('*')):
                    if path.is_symlink():raise ValueError('A backup input contains a symbolic link.')
                    if path.is_file() and not path.name.startswith('.') and not path.name.endswith(('.part','.partial','.importing')):content.append(path)
            for path in content:
                if shutil.disk_usage(destination.parent).free<path.stat().st_size+policy['reserve_bytes']:raise ValueError('The backup reached the free-space reserve.')
                before=path.stat();sha=digest(path);name=path.relative_to(root).as_posix();archive.write(path,name)
                if path.stat().st_size!=before.st_size or digest(path)!=sha:raise ValueError('A file changed during backup. Repeat the backup after work stops.')
                files.append({'path':name,'bytes':before.st_size,'sha256':sha})
            data=json_bytes(policy);archive.writestr('storage.json',data);files.append({'path':'storage.json','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            document={'contract':'desktop-backup/1','includes_observations':include_observations,'migrations':migrations,'tables':table_list,'files':files}
            validate(payload,'records/desktop-backup/v1.schema.json',document);archive.writestr('backup.json',json_bytes(document))
        inspect(payload,temporary)
        os.link(temporary,destination)
    finally:temporary.unlink(missing_ok=True)
    return {'path':str(destination),'files':len(files),'includes_observations':include_observations,'bytes':destination.stat().st_size}


def inspect(payload,path):
    with zipfile.ZipFile(path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        if len(names)!=len(set(names)) or len(names)>MAX_FILES or sum(i.file_size for i in infos)>MAX_BACKUP_BYTES:raise ValueError('The backup exceeds its file limits or repeats a filename.')
        if archive.getinfo('backup.json').file_size>32*1024**2:raise ValueError('The backup manifest is too large.')
        document=json.loads(archive.read('backup.json'));validate(payload,'records/desktop-backup/v1.schema.json',document)
        if set(names)!={'backup.json'}|{i['path'] for i in document['files']} or len(document['files'])!=len(names)-1:raise ValueError('The backup file list is inconsistent.')
        for info in infos:
            parts=Path(info.filename).parts
            if info.filename.startswith('/') or '\\' in info.filename or '..' in parts or str(Path(info.filename))!=info.filename or info.is_dir() or stat.S_ISLNK(info.external_attr>>16):raise ValueError('The backup contains an unsafe path.')
            if info.filename not in ('backup.json','storage.json') and not info.filename.startswith(('database/','raw/tess-spoc-light-curves/','artifacts/','reproductions/')):raise ValueError('The backup contains an unsupported file.')
        for item in document['files']:
            with archive.open(item['path']) as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
            if archive.getinfo(item['path']).file_size!=item['bytes'] or sha!=item['sha256']:raise ValueError('A backup file failed its integrity check.')
        known=sorted((payload/'components/database/migrations').glob('[0-9]*.sql'))
        versions=document['migrations']
        if len(versions)>len(known):raise ValueError('This backup requires a newer application.')
        for recorded,source in zip(versions,known):
            if recorded!={'version':source.stem,'sha256':digest(source)}:raise ValueError('The backup migration hashes do not match this application.')
        if {i['path'] for i in document['files'] if i['path'].startswith('database/')}!={'database/'+t['name']+'.csv' for t in document['tables']}:raise ValueError('The backup table list is inconsistent.')
        return document


def restore(payload,archive_path,destination):
    document=inspect(payload,archive_path)
    if destination.exists() and any(destination.iterdir()):raise ValueError('Restore into an empty directory. The original workspace stays unchanged.')
    needed=sum(i['bytes'] for i in document['files'])+512*1024**2
    parent=destination.parent
    if shutil.disk_usage(parent).free<needed+512*1024**2:raise ValueError('The restore destination needs more free space.')
    if len(str(destination/'socket').encode())>85:raise ValueError('Choose a shorter restore path for the database socket.')
    lock=workspace_lock(destination);pg=payload/'postgres/bin';env=environment(payload,destination,'api');started=False
    try:
        for name in ('logs','socket','tmp','home','database','raw/tess-spoc-light-curves','artifacts'):(destination/name).mkdir(mode=0o700,parents=True,exist_ok=True)
        atomic_text(destination/'restore-in-progress','The restore must finish before normal startup.\n')
        run_logged([str(pg/'initdb'),'-D',str(destination/'database'),'-U','delta','--encoding=UTF8','--locale=C','--auth-local=trust','--auth-host=reject'],env,destination/'logs/restore.log')
        options=shlex.join(['-h','','-k',str(destination/'socket'),'-c','shared_buffers=64MB','-c','max_connections=20'])
        run_logged([str(pg/'pg_ctl'),'-D',str(destination/'database'),'-l',str(destination/'logs/postgres.log'),'-w','-o',options,'start'],env,destination/'logs/restore.log');started=True
        url=database_url(destination)
        with psycopg.connect(url.replace('/delta?','/postgres?'),autocommit=True) as conn:conn.execute('CREATE DATABASE delta')
        with psycopg.connect(url,row_factory=dict_row) as conn:
            conn.execute('CREATE TABLE schema_migration(version text PRIMARY KEY,sha256 text NOT NULL,applied_at timestamptz NOT NULL DEFAULT now())')
            for migration in document['migrations']:
                source=payload/'components/database/migrations'/(migration['version']+'.sql')
                conn.execute(source.read_text());conn.execute('INSERT INTO schema_migration(version,sha256) VALUES(%s,%s)',[migration['version'],migration['sha256']])
            if tables(conn)!=document['tables']:raise ValueError('The backup tables differ from the trusted migration schema.')
            constraints=conn.execute("SELECT c.conname,c.conrelid::regclass::text AS table_name,pg_get_constraintdef(c.oid) AS definition FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public' AND c.contype='f' ORDER BY c.conname").fetchall()
            for constraint in constraints:conn.execute(sql.SQL('ALTER TABLE {} DROP CONSTRAINT {}').format(sql.Identifier(constraint['table_name']),sql.Identifier(constraint['conname'])))
            conn.execute("SET LOCAL session_replication_role='replica'")
            # Only COPY values enter the database. No archive text becomes an SQL command.
            with zipfile.ZipFile(archive_path) as archive:
                for table in document['tables']:
                    statement=sql.SQL('COPY {} ({}) FROM STDIN WITH (FORMAT CSV)').format(sql.Identifier(table['name']),sql.SQL(',').join(map(sql.Identifier,table['columns'])))
                    with archive.open('database/'+table['name']+'.csv') as source,conn.cursor().copy(statement) as copy:
                        while block:=source.read(1024**2):copy.write(block)
                for item in document['files']:
                    if item['path'].startswith('database/'):continue
                    target=destination/item['path'];target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                    with archive.open(item['path']) as source,target.open('xb') as out:shutil.copyfileobj(source,out,1024**2)
                    target.chmod(0o600)
            for constraint in constraints:conn.execute(sql.SQL('ALTER TABLE {} ADD CONSTRAINT {} ').format(sql.Identifier(constraint['table_name']),sql.Identifier(constraint['conname']))+sql.SQL(constraint['definition']))
            for table in document['tables']:
                for column in table['columns']:
                    sequence=conn.execute('SELECT pg_get_serial_sequence(%s,%s) AS name',[table['name'],column]).fetchone()['name']
                    if sequence:
                        maximum=conn.execute(sql.SQL('SELECT max({}) AS n FROM {}').format(sql.Identifier(column),sql.Identifier(table['name']))).fetchone()['n']
                        conn.execute('SELECT setval(%s,%s,%s)',[sequence,maximum or 1,maximum is not None])
            token=secrets.token_urlsafe(32)
            for client in conn.execute('SELECT id FROM client').fetchall():
                conn.execute('UPDATE client SET token_sha256=%s WHERE id=%s',[hashlib.sha256(secrets.token_bytes(32)).hexdigest(),client['id']])
            owner=conn.execute("UPDATE client SET token_sha256=%s,disabled_at=NULL WHERE name='desktop-owner' AND kind='person' RETURNING id",[hashlib.sha256(token.encode()).hexdigest()]).fetchone()
            if owner is None:raise ValueError('The backup has no desktop owner.')
            conn.execute("UPDATE client SET disabled_at=NULL WHERE name='desktop-reader' AND kind='service'")
            conn.execute("UPDATE job SET state='queued',claimed_by=NULL,lease_expires_at=NULL,attempts=GREATEST(attempts-1,0) WHERE state='running'")
            if conn.execute("SELECT to_regclass('agent_session') AS name").fetchone()['name']:
                conn.execute("UPDATE agent_session SET document=jsonb_set(document,'{state}','\"paused\"') WHERE document->>'state'<>'closed'")
            conn.execute("SET LOCAL session_replication_role='origin'")
        atomic_text(destination/'owner.token',token+'\n')
        (destination/'restore-in-progress').unlink()
        return {'workspace':str(destination),'files':len(document['files']),'message':'The backup restored into a separate workspace. Access credentials were regenerated.'}
    finally:
        if started:run_logged([str(pg/'pg_ctl'),'-D',str(destination/'database'),'-w','-m','fast','stop'],env,destination/'logs/restore.log')
        lock.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,required=True);parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('action',choices=['backup','restore','inspect']);parser.add_argument('--path',type=Path,required=True);parser.add_argument('--destination',type=Path);parser.add_argument('--without-observations',action='store_true');args=parser.parse_args()
    if args.action=='backup':result=backup(args.payload,args.workspace,args.path,not args.without_observations)
    elif args.action=='restore':result=restore(args.payload,args.path,args.destination)
    else:result=inspect(args.payload,args.path)
    print(json.dumps(result))

if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'error':str(error)}));raise SystemExit(1)
