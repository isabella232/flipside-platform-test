#!/usr/bin/python3
'''Install and configure salt on the local machine.'''
import subprocess
import json
import time
import urllib.request
import tempfile
import os


def install_salt(standalone, version='stable'):
    '''Install Salt on the local machine'''
    resp = urllib.request.urlopen('https://bootstrap.saltstack.com')
    assert resp.status == 200
    with tempfile.NamedTemporaryFile(mode='w+b') as f:
        f.write(resp.read())
        f.flush()
        subprocess.check_call(
            'sh {script} {opts} -n -p python-git {version}'.format(
                script=f.name,
                opts='-M -N -X' if standalone else '-i local -A 127.0.0.1',
                version=version
            ).split()
        )


def setup_salt(standalone):
    # XXX Maybe we could simply use salt to... bootstrap salt
    if not os.path.exists('/etc/salt/master.d'):
        os.mkdir('/etc/salt/master.d')
    with open('/etc/salt/master.d/flipside_gitfs', 'w+') as f:
        f.write('fileserver_backend:\n  - roots\n  - gitfs\n\ngitfs_remotes:\n  - https://github.com/saltstack-formulas/nginx-formula.git')
    if standalone:
        # XXX use minion.d instead
        with open('/etc/salt/minion', 'w+') as f:
            f.write('file_client:\n  local\n')
    else:
        time.sleep(1)
        subprocess.check_call('sudo salt-key -Ay'.split())


def test_salt(standalone):
    if standalone:
        return
    for i in range(2):
        ping = json.loads(
            subprocess.check_output(
                'sudo salt * test.ping --out json --static'.split()
            ).decode()
        )
    if ping.get('local'):
        print('OK')
    else:
        raise SystemExit('ERROR')


def highstate_salt(standalone):
    subprocess.check_call('sudo salt-call state.highstate'.split())


def main(standalone=True, highstate=True, salt_version=None):
    install_salt(standalone)
    setup_salt(standalone)
    test_salt(standalone)
    if highstate:
        highstate_salt(standalone)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-standalone', action='store_true')
    parser.add_argument('--no-highstate', action='store_true')
    parser.add_argument('--salt-version', default='stable')
    args = parser.parse_args()
    main(standalone=not args.no_standalone, highstate=not args.no_highstate,
         salt_version=args.salt_version)
