#!/usr/bin/env python3
"""Builds the Kegeln mod.

    python scripts/build.py                 build into dist/kegeln
    python scripts/build.py --dev           same, with test hotkeys (Shift+F6 invitation, Shift+F7 scratch script)
    python scripts/build.py --zip           also write dist/kegeln-v<version>.zip and its .sha256
    python scripts/build.py --install DIR   also copy the mod into DIR (your "Anno 117 - Pax Romana/mods" folder)
    python scripts/build.py --version 0.2.0 set the version in modinfo.json and the zip name

The three parts run in order: build_base.py (modinfo, emperor invitation, timer), build_trichter.py (goods, need,
buildings, build menu) and build_contracts.py (lighthouse delivery contracts). Python 3.9+ and no extra packages.
"""
import argparse, hashlib, os, shutil, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOD_FOLDER = 'kegeln'


def main():
    ap = argparse.ArgumentParser(description='Build the Kegeln mod for Anno 117.')
    ap.add_argument('--dev', action='store_true', help='include test hotkeys')
    ap.add_argument('--zip', action='store_true', help='write a release zip with checksum')
    ap.add_argument('--install', metavar='DIR', help='copy the built mod into this mods folder')
    ap.add_argument('--version', default='0.1.0')
    ap.add_argument('--vanilla-assets', metavar='FILE', help="the game's assets.xml, only needed to refresh vanilla_templates.json")
    args = ap.parse_args()

    dist = os.path.join(ROOT, 'dist')
    out = os.path.join(dist, MOD_FOLDER)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    env = dict(os.environ, KEGELN_VERSION=args.version)

    def run(script, *extra):
        subprocess.run([sys.executable, os.path.join(HERE, script), out, *extra], check=True, env=env)

    run('build_base.py', *(['--dev'] if args.dev else []))
    run('build_trichter.py', *([args.vanilla_assets] if args.vanilla_assets else []))
    run('build_contracts.py')

    if args.zip:
        name = f'kegeln-v{args.version}.zip'
        path = os.path.join(dist, name)
        files = sorted(os.path.join(d, f) for d, _, fs in os.walk(out) for f in fs)
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in files:
                info = zipfile.ZipInfo(MOD_FOLDER + '/' + os.path.relpath(f, out).replace(os.sep, '/'), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, open(f, 'rb').read())
        digest = hashlib.sha256(open(path, 'rb').read()).hexdigest()
        open(path + '.sha256', 'w', newline='\n').write(f'{digest}  {name}\n')
        print('zip:', path, digest)

    if args.install:
        dst = os.path.join(args.install, MOD_FOLDER)
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(out, dst)
        print('installed:', dst)
    print('built:', out)


if __name__ == '__main__':
    main()
