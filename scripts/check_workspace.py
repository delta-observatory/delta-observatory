"""Check workspace documentation, registers, syntax, hashes, and generated-file hygiene."""
import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
# Documents link to other repositories of the GitHub organization by address.
# The check maps each address to the local sibling directory.
ORGANIZATION_LINK = re.compile(r'^https://github\.com/delta-observatory/([A-Za-z0-9._-]+)/(?:blob|tree)/main/([^#?\s]*)(?:#(\S*))?$')


# Application repositories run tests and builds locally. Their Git exclusion
# rules ignore these generated folders, so the scan skips them there.
APPLICATION_REPOSITORIES = {'backend', 'database', 'frontend', 'kubernetes', 'workers'}
APPLICATION_GENERATED = {'__pycache__', 'node_modules', 'dist', 'build', 'coverage'}


def visible_files():
    files = []
    for directory, folders, names in os.walk(ROOT):
        top = Path(directory).relative_to(ROOT).parts[:1]
        generated = APPLICATION_GENERATED if top and top[0] in APPLICATION_REPOSITORIES else set()
        folders[:] = [name for name in folders if not name.startswith('.') and name not in generated
                      and not (Path(directory) == ROOT and name == 'raw')]
        files.extend(Path(directory)/name for name in names if not name.startswith('.'))
    return sorted(files)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def content_without_fences(text):
    return re.sub(r'```[^\n]*\n.*?```', '', text, flags=re.S)


def heading_ids(text):
    ids = set(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    seen = Counter()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*\s*$', content_without_fences(text), re.M):
        heading = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', heading)
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        suffix = '' if seen[slug] == 0 else '-'+str(seen[slug])
        seen[slug] += 1
        ids.add(slug+suffix)
    return ids


def check():
    files = visible_files()
    counts = Counter(files=len(files))
    errors = []
    data = {}

    def require(condition, message):
        if not condition:
            errors.append(message)

    def invalid_constant(value):
        raise ValueError('Non-standard JSON constant: '+value)

    def local_file(base, value, label):
        target = value.split('#')[0]
        path = (base/unquote(target)).resolve()
        require(path.is_file(), label+': missing '+value)
        return path

    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        if path.suffix == '.json':
            try:
                data[path] = json.loads(path.read_text(), parse_constant=invalid_constant)
                counts['json_files'] += 1
            except (ValueError, OSError) as error:
                errors.append(relative+': '+str(error))
        if path.suffix == '.py':
            try:
                ast.parse(path.read_text(), filename=relative)
                counts['python_files'] += 1
            except (SyntaxError, OSError) as error:
                errors.append(relative+': '+str(error))
        if path.suffix == '.md':
            counts['markdown_files'] += 1
            text = content_without_fences(path.read_text())
            for value in re.findall(r'\]\(([^\n]+?)\)', text):
                value = value.split(' "')[0].strip('<>')
                linked = ORGANIZATION_LINK.match(value)
                if linked:
                    repository, name, fragment = linked.group(1), linked.group(2), linked.group(3) or ''
                    target = (ROOT if repository == 'delta-observatory' else ROOT/repository)/unquote(name)
                    counts['organization_links'] += 1
                elif value.startswith(('https://', 'http://', 'mailto:')):
                    continue
                else:
                    name, _, fragment = value.partition('#')
                    target = path.parent/unquote(name) if name else path
                    counts['local_markdown_links'] += 1
                require(target.exists(), relative+': missing link '+value)
                if fragment and target.is_file() and target.suffix == '.md':
                    require(unquote(fragment) in heading_ids(target.read_text()),
                            relative+': missing heading '+value)
                    counts['local_heading_links'] += 1
        if '__pycache__' in path.parts or path.suffix in {'.pyc', '.part', '.tmp', '.orig', '.rej'}:
            errors.append(relative+': unexpected generated or unfinished file')
        if relative.startswith('experiments/') and path.name.lower().endswith(
                ('.fits', '.fits.fz', '.fit', '.fts', '.npy', '.npz')):
            errors.append(relative+': observation or array belongs outside experiment records')

    for name in ['README.md', 'WORKSPACE.md', 'AGENTS.md', 'DESIGN.md', 'ROADMAP.md', 'REFERENCE-CATALOGS.md',
                 'CHECKS.md', 'experiments/PROCEDURE.md', 'experiments/AGENTS.md',
                 'experiments/README.md', 'experiments/PLAN.md',
                 'experiments/planning/experiment-template.md']:
        require((ROOT/name).is_file(), 'Missing workspace entry point: '+name)

    catalog = data.get(ROOT/'datasets/catalog.json', {})
    entries = catalog.get('entries', [])
    dataset_ids = {record['id'] for record in entries}
    require(len(dataset_ids) == len(entries), 'Duplicate dataset IDs')
    require(catalog.get('entry_count') == len(entries), 'Dataset catalog count differs')
    directories = {p.name for p in (ROOT/'datasets').iterdir() if p.is_dir() and not p.name.startswith('.')}
    require(directories == dataset_ids, 'Dataset directories differ from catalog IDs')
    for entry in entries:
        for key in ['description', 'metadata', 'acquisition']:
            local_file(ROOT/'datasets', entry[key], entry['id'])
        metadata_path = ROOT/'datasets'/entry['metadata']
        metadata = data.get(metadata_path, {})
        for key in ['id', 'name', 'category', 'kind']:
            require(entry[key] == metadata.get(key), entry['id']+': catalog '+key+' differs from metadata')
        for related in metadata.get('related_dataset_ids', []):
            require(related in dataset_ids, entry['id']+': unknown related dataset '+related)
        evidence = metadata.get('acquisition', {}).get('verification', {}).get('evidence')
        if evidence:
            local_file(metadata_path.parent, evidence, entry['id'])
    counts['dataset_entries'] = len(entries)
    if (ROOT/'raw').is_dir():
        for path in sorted((ROOT/'raw').iterdir()):
            if path.name.startswith('.'):
                continue
            if not path.is_dir():
                errors.append('raw/'+path.name+': observations belong in raw/<dataset-id>/')
                continue
            require(path.name in dataset_ids, 'raw/'+path.name+': directory name is not a dataset ID in datasets/')
            counts['raw_dataset_directories'] += 1
    declared = re.search(r'catalogue contains (\d+)', (ROOT/'datasets/README.md').read_text())
    require(declared is not None and int(declared.group(1)) == len(entries), 'Dataset README count differs')

    register = data.get(ROOT/'experiments/planning/tasks.json', {})
    for key in ['procedure', 'protocol_template']:
        name = register.get(key)
        require(bool(name), 'Task register lacks its '+key+' reference')
        if name:
            local_file(ROOT/'experiments/planning', name, key)
    tasks = register.get('tasks', [])
    task_map = {task['id']: task for task in tasks}
    require(len(task_map) == len(tasks), 'Duplicate scientific task IDs')
    mandatory_edges = set()
    conditional_edges = set()
    for task in tasks:
        for dependency in task['depends_on']:
            require(dependency in task_map, task['id']+': unknown dependency '+dependency)
            mandatory_edges.add((dependency, task['id']))
        for dependency in task['conditional_dependencies']:
            require(dependency['task'] in task_map, task['id']+': unknown conditional dependency')
            conditional_edges.add((dependency['task'], task['id']))
        for name in task['source_records']+[task['plan_section']]:
            target = local_file(ROOT/'experiments/planning', name, task['id'])
            if '#' in name and target.is_file():
                require(name.partition('#')[2] in heading_ids(target.read_text()), task['id']+': missing plan heading')
        if task.get('closure_record'):
            local_file(ROOT/'experiments/planning', task['closure_record'], task['id'])
    visited, active = set(), set()

    def visit(identifier):
        if identifier in active:
            errors.append('Scientific task dependency cycle at '+identifier)
            return
        if identifier in visited or identifier not in task_map:
            return
        active.add(identifier)
        for before, after in mandatory_edges | conditional_edges:
            if after == identifier:
                visit(before)
        active.remove(identifier)
        visited.add(identifier)

    for identifier in task_map:
        visit(identifier)
    plan = (ROOT/'experiments/PLAN.md').read_text()
    id_pattern = r'([AGT]\d{2})(?:\[[^\]]*\])?'
    diagram_mandatory = set(re.findall(r'^\s*'+id_pattern+r'\s*-->\s*([AGT]\d{2})', plan, re.M))
    diagram_conditional = set(re.findall(r'^\s*'+id_pattern+r'\s*-\.\s+.+?\s+\.->\s*([AGT]\d{2})', plan, re.M))
    require(diagram_mandatory == mandatory_edges, 'Plan diagram differs from mandatory task dependencies')
    require(diagram_conditional == conditional_edges, 'Plan diagram differs from conditional task dependencies')
    counts['scientific_tasks'] = len(tasks)

    experiment_files = sorted((ROOT/'experiments').glob('*/experiment.json'))
    index = (ROOT/'experiments/README.md').read_text()
    indexed = set(re.findall(r'\]\(([^/)]+)/README\.md\)', index))
    recorded = {path.parent.name for path in experiment_files}
    require(recorded <= indexed, 'An experiment is missing from the experiment index')
    require(indexed-{p for p in indexed if p in ['planning', 'reviews']} == recorded,
            'Experiment index and registered experiment directories differ')
    for path in experiment_files:
        record = data.get(path, {})
        if record.get('contract_version') == 1:
            require(record.get('id') == path.parent.name, path.parent.name+': experiment ID differs')
            require(set(record.get('datasets', [])) <= dataset_ids, path.parent.name+': unknown dataset ID')
            require(record.get('task_id') in task_map, path.parent.name+': unknown plan task')
            for method in record.get('methods', []):
                local_file(ROOT/'detection', method+'/README.md', path.parent.name)
            for value in record.get('records', {}).values():
                if record.get('record_status') == 'closed':
                    local_file(path.parent, value, path.parent.name)
            continue
        require(record.get('experiment_id') == path.parent.name, path.parent.name+': experiment ID differs')
        for dataset in record.get('datasets', []):
            require(dataset['dataset_id'] in dataset_ids, path.parent.name+': unknown dataset ID')
            target = local_file(path.parent, dataset['record'], path.parent.name)
            require(target.parent.name == dataset['dataset_id'], path.parent.name+': dataset path differs from ID')
        for method in record.get('detection_methods', []):
            target = local_file(path.parent, method['record'], path.parent.name)
            require(target.parent == ROOT/'detection'/method['method_id'], path.parent.name+': method path differs from ID')
        for required in ['README.md', 'config.json', 'inputs.json']:
            require((path.parent/required).is_file(), path.parent.name+': missing '+required)
    counts['registered_experiments'] = len(experiment_files)
    closed = sum(1 for line in index.splitlines()
                 if re.match(r'^\| \[.+\]\([^/)]+/README\.md\) \| Closed', line))
    declared = re.search(r'records (\d+) completed bounded investigations', (ROOT/'WORKSPACE.md').read_text())
    require(declared is not None and int(declared.group(1)) == closed, 'Workspace guide completed-experiment count differs')
    counts['closed_experiments_in_index'] = closed

    sources = data.get(ROOT/'detection/sources.json', [])
    retrieved = data.get(ROOT/'detection/retrieval-manifest.json', [])
    source_map = {record['id']: record for record in sources}
    retrieved_map = {record['id']: record for record in retrieved}
    require(len(source_map) == len(sources), 'Duplicate source IDs')
    require(len(retrieved_map) == len(retrieved), 'Duplicate retrieval IDs')
    require(set(source_map) == set(retrieved_map), 'Source and retrieval IDs differ')
    for identifier, source in source_map.items():
        retrieval = retrieved_map.get(identifier, {})
        if retrieval.get('status') != 'downloaded':
            require(bool(retrieval.get('error')), identifier+': unavailable source lacks a reason')
            counts['unavailable_source_files'] += 1
            continue
        path = local_file(ROOT/'detection', source['path'], identifier)
        if path.is_file():
            require(path.stat().st_size == retrieval['bytes'], identifier+': PDF size differs')
            require(sha(path) == retrieval['sha256'], identifier+': PDF hash differs')
            with path.open('rb') as stream:
                require(stream.read(5) == b'%PDF-', identifier+': PDF header differs')
            counts['pdf_hashes'] += 1
    counts['source_records'] = len(sources)
    domain_methods = sum(len(list((ROOT/'detection'/name).glob('*/README.md')))
                         for name in ['asteroids', 'exoplanets', 'solar-system-planets'])
    counts['domain_method_chapters'] = domain_methods
    counts['method_chapters_including_machine_learning'] = domain_methods+int((ROOT/'detection/machine-learning/README.md').is_file())

    for path, record in data.items():
        if path.name not in ['freeze.json', 'scripts-manifest.json', 'closure-check.json']:
            continue
        if not isinstance(record, dict) or not isinstance(record.get('files'), dict):
            continue
        for name, expected in record['files'].items():
            target = local_file(path.parent, name, str(path.relative_to(ROOT)))
            if target.is_file():
                require(sha(target) == expected, str(target.relative_to(ROOT))+': frozen hash differs')
                counts['experiment_manifest_hashes'] += 1
    legacy_closure = data.get(ROOT/'experiments/closure-check.json', {})
    for record in legacy_closure.get('records', []):
        path = ROOT/'experiments'/record['experiment']/'inputs.json'
        require(sha(path) == record['input_manifest_sha256'], record['experiment']+': legacy input manifest differs')
        counts['legacy_input_manifest_hashes'] += 1

    registry_check = subprocess.run([sys.executable, '-B', str(ROOT/'experiments/scripts/cohort_registry.py'),
                                     str(ROOT/'experiments/cohorts.json')], capture_output=True, text=True, timeout=20)
    require(registry_check.returncode == 0, 'Shared cohort register failed: '+registry_check.stdout+registry_check.stderr)
    if registry_check.returncode == 0:
        counts['cohort_reservations'] = json.loads(registry_check.stdout)['entries']
    support = data.get(ROOT/'experiments/support-check.json')
    if support:
        require(support.get('status') == 'passed', 'Support regression checks did not pass')
        for name, expected in support.get('files', {}).items():
            require(sha(ROOT/'experiments'/name) == expected, 'Support check is stale: '+name)

    repositories = {}
    unavailable_at = []
    locations = ['.', 'datasets', 'detection', 'experiments', 'database',
                 'workers', 'backend', 'frontend', 'kubernetes', 'agents', 'community']
    for location in locations:
        try:
            identity = subprocess.run(['git', '-C', str(ROOT/location), 'rev-parse', '--show-toplevel'],
                                      capture_output=True, text=True, timeout=10)
            if identity.returncode:
                unavailable_at.append(location)
                continue
            repository = identity.stdout.strip()
            require(Path(repository).resolve() == (ROOT/location).resolve(), 'Repository boundary differs: '+location)
            if repository in repositories:
                continue
            result = subprocess.run(['git', '-C', repository, 'status', '--porcelain'],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode:
                unavailable_at.append(location)
                continue
            repositories[repository] = dict(working_tree_clean=not bool(result.stdout.strip()),
                                            changes=result.stdout.splitlines())
            branch = subprocess.run(['git', '-C', repository, 'symbolic-ref', '--short', 'HEAD'], capture_output=True, text=True)
            head = subprocess.run(['git', '-C', repository, 'rev-parse', '--verify', 'HEAD'], capture_output=True, text=True)
            remote = subprocess.run(['git', '-C', repository, 'remote'], capture_output=True, text=True)
            repositories[repository].update(branch=branch.stdout.strip(), has_commits=head.returncode == 0,
                                            remote_names=remote.stdout.splitlines())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            unavailable_at.append(location)
    version_control = dict(status='available' if repositories else 'unavailable',
                           directories_checked=len(locations), repositories=repositories,
                           unavailable_at=unavailable_at,
                           working_tree_clean=(all(r['working_tree_clean'] for r in repositories.values())
                                               if repositories else None))
    return dict(status='passed' if not errors else 'failed', checked_utc=datetime.now(timezone.utc).isoformat(),
                checker_sha256=sha(Path(__file__)),
                scope='Local documentation, catalogs, dependencies, syntax, retained hashes, and generated-file hygiene.',
                counts=dict(counts), errors=errors, version_control=version_control,
                limits=['No remote URL availability check.', 'No scientific processing or candidate validation.',
                        'Run check_experiment.py separately with original inputs for full version-1 record checks.',
                        'No complete ASD-STE100 dictionary check.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = check()
    if args.output:
        with args.output.open('x') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)
