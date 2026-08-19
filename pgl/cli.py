from __future__ import annotations
import argparse,json
from pathlib import Path
from .config import load_config
from .pipeline import run_sync
from .doctor import run_doctor
from .history.stats import build_stats
from .util import load_json, atomic_json
from .resolve.mappings import load_mappings
from .associations import associate
from .output.jekyll import output_paths
from .install import InstallError, install_chirpy, format_actions

VERSION='0.1.0-alpha.5'

def _history_from_disk(root: Path):
    _,assets=output_paths(root); events=[]
    hdir=assets/'history'
    if hdir.exists():
        for p in sorted(hdir.glob('*.json')):
            events.extend(load_json(p,{'events':[]}).get('events',[]))
    return events

def _associate_only(root: Path, cfg: dict, dry_run: bool=False):
    data,assets=output_paths(root)
    library=load_json(data/'library.json',{'schema_version':1,'items':[]})
    items=library.get('items',[])
    mappings=load_mappings(data/'mappings.yml')
    associations=associate(root,items,cfg,mappings) if cfg.get('association',{}).get('enabled',True) else {'by_entity':{},'by_post':{},'suggestions':[]}
    for item in items:
        item['articles']=associations.get('by_entity',{}).get(item.get('id'),[])
    if not dry_run:
        atomic_json(data/'associations.json',associations)
        atomic_json(data/'diagnostics'/'associations.json',{'suggestions':associations.get('suggestions',[])})
        atomic_json(data/'library.json',library)
        atomic_json(assets/'library.json',library)
    return library,associations

def main(argv=None):
    p=argparse.ArgumentParser(prog='pgl',description='Prospero Great Library')
    p.add_argument('--version',action='version',version=VERSION)
    sub=p.add_subparsers(dest='cmd',required=True)
    for name in ('sync','build-data'):
        s=sub.add_parser(name); s.add_argument('--site-root',default='.'); s.add_argument('--config',default='_config.yml'); s.add_argument('--fixtures'); s.add_argument('--dry-run',action='store_true')
    d=sub.add_parser('doctor'); d.add_argument('--site-root',default='.'); d.add_argument('--config',default='_config.yml')
    a=sub.add_parser('associate-posts'); a.add_argument('--site-root',default='.'); a.add_argument('--config',default='_config.yml'); a.add_argument('--dry-run',action='store_true')
    st=sub.add_parser('stats'); st.add_argument('--site-root',default='.')
    pa=sub.add_parser('privacy-audit'); pa.add_argument('--site-root',default='.'); pa.add_argument('--config',default='_config.yml'); pa.add_argument('--fixtures'); pa.add_argument('--apply',action='store_true')
    ins=sub.add_parser('install'); ins.add_argument('--adapter',choices=['chirpy'],default='chirpy'); ins.add_argument('--site-root',default='.'); ins.add_argument('--dry-run',action='store_true'); ins.add_argument('--force',action='store_true'); ins.add_argument('--no-backup',action='store_true')
    args=p.parse_args(argv)
    if args.cmd in ('sync','build-data'):
        root=Path(args.site_root); cfg=load_config(root/args.config)
        result=run_sync(root,cfg,getattr(args,'fixtures',None),getattr(args,'dry_run',False))
        print(json.dumps({'overall':result['sync_status']['overall'],'items':len(result['library']['items']),'events':len(result['events']),'suggestions':len(result['associations'].get('suggestions',[]))},ensure_ascii=False,indent=2))
        return 0
    if args.cmd=='associate-posts':
        root=Path(args.site_root); cfg=load_config(root/args.config)
        library,associations=_associate_only(root,cfg,args.dry_run)
        print(json.dumps({'items':len(library.get('items',[])),'linked_entities':len(associations.get('by_entity',{})),'linked_posts':len(associations.get('by_post',{})),'suggestions':len(associations.get('suggestions',[]))},ensure_ascii=False,indent=2))
        return 0
    if args.cmd=='privacy-audit':
        root=Path(args.site_root); cfg=load_config(root/args.config)
        result=run_sync(root,cfg,getattr(args,'fixtures',None),dry_run=not args.apply)
        report=result.get('diagnostics',{}).get('privacy',{})
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 1 if report.get('public_output_violations') else 0
    if args.cmd=='install':
        try:
            actions=install_chirpy(Path(args.site_root),dry_run=args.dry_run,force=args.force,backup=not args.no_backup)
        except InstallError as exc:
            print(f'ERROR {exc}')
            return 2
        print(format_actions(actions))
        return 2 if any(x.action=='conflict' for x in actions) else 0
    if args.cmd=='doctor':
        root=Path(args.site_root); checks=run_doctor(root,load_config(root/args.config))
        for c in checks: print(('OK  ' if c['ok'] else 'WARN')+f" {c['check']}: {c['detail']}")
        return 0 if all(c['ok'] for c in checks if c['check']!='library_page') else 1
    if args.cmd=='stats':
        root=Path(args.site_root); lib=load_json(root/'_data'/'prospero_great_library'/'library.json',{'items':[]})
        print(json.dumps(build_stats(lib.get('items',[]),_history_from_disk(root)),ensure_ascii=False,indent=2)); return 0
    return 2

if __name__=='__main__': raise SystemExit(main())
