from __future__ import absolute_import
from __future__ import print_function

import sys
import os
import logging
import json
import subprocess
from decorator import decorator

docker_path = '/usr/bin/docker'
default_cmd = ['/bin/sh']

common_run_args = [
    '--name', '{name}',
    '-v', '/etc/localtime:/etc/localtime',
    '-e', 'ATOMIC_NAME={name}',
    '-e', 'ATOMIC_IMAGE={image}',
]

interactive_run_args = [
    '-i', '--rm',
]

persistent_run_args = [
    '-d',
]

spc_run_args = [
    '--privileged',
    '--net=host',
    '--ipc=host',
    '--pid=host',
    '-e', 'ATOMIC_SPC=1',
    '-v', '/:/host',
    '-v', '/run:/run',
    '-e', 'ATOMIC_HOST=/host',
]


def idocker(*args):
    cmd = [docker_path] + list(args)
    subprocess.check_call(cmd)


def docker(*args):
    cmd = [docker_path] + list(args)
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, output=stdout)

    return stdout


def is_namespaced(name):
    return (':' in name
            or '.' in name
            or name.isupper())


class Inspectable(dict):
    log = logging.getLogger(__name__)

    def __init__(self, name):
        self.name = name
        self.refresh()

    def inspect(self):
        res = docker('inspect', self.name)
        res = json.loads(res)
        return res[0]

    def refresh(self):
        try:
            res = self.inspect()
            self._exists = True
            self.clear()
            self.update(res)
        except subprocess.CalledProcessError as err:
            self._exists = False

    def exists(self):
        return self._exists

    @property
    def config(self):
        return self['Config']

    @property
    def labels(self):
        if self.config['Labels'] is None:
            return {}

        return self.config['Labels']

    def get_boolean_label(self, label):
        val = self.labels.get(label, 'false')
        return val.lower() in ['1', 'true', 'yes']

    @property
    def id(self):
        return self.get('Id')


@decorator
def pim(func, self, *args, **kw):
    self.pull_if_missing()
    return func(self, *args, **kw)


@decorator
def refresh(func, self, *args, **kw):
    res = func(self, *args, **kw)
    self.refresh()
    return res


class Image (Inspectable):
    def default_container_name(self):
        name = self.name.split('/')[-1].split(':')[0]
        return name

    @refresh
    def pull(self):
        self.log.info('pulling image %s', self.name)
        idocker('pull', self.name)

    def pull_if_missing(self):
        if not self.exists():
            self.pull()

    def update_image(self, force=True):
        if force:
            self.force_delete_containers()

        self.pull()

    def force_delete_containers(self):
        self.log.warn('deleting containers using image %s',
                      self.name)
        res = docker('ps', '-aq', '--no-trunc')
        for id in res.splitlines():
            c = Container(id)
            if c['Image'] == self.id:
                self.log.warn('deleting container %s',
                              c.name)
                c.delete(force=True)

    def command(self):
        cmd = self.config.get('Cmd') or default_cmd
        return cmd

    @pim
    def info(self):
        info = dict((k, v) for k, v in self.labels.items()
                    if not is_namespaced(k))
        return info

    @pim
    def extra_info(self):
        info = dict((k, v) for k, v in self.labels.items()
                    if is_namespaced(k))

        return info

    @pim
    def version(self):
        try:
            return (self.labels[field]
                    for field in ['Name', 'Version', 'Release'])
        except KeyError:
            pass


class Container (Inspectable):
    def is_running(self):
        return self.exists() and self['State']['Running']

    def is_interactive(self):
        return self.exists() and all((self['Config'][opt] is True
                                      for opt in ['AttachStdin',
                                                  'AttachStdout',
                                                  'AttachStderr']))

    @property
    def pid(self):
        return self.get('State', {}).get('Pid')

    @property
    def address(self):
        return self.get('NetworkSettings', {}).get('IPAddress')

    @refresh
    def delete(self, force=False):
        self.log.info('deleting container %s',
                      self.name)
        cmd = ['rm']
        if force:
            cmd.append('--force')
        cmd.append(self.id)
        idocker(*cmd)

    @refresh
    def start(self):
        if self.is_running():
            self.log.info('not starting container %s: '
                          'container is already running',
                          self.name)
            return

        self.log.info('starting container %s',
                      self.name)
        idocker('start', self.name)

    @refresh
    def stop(self):
        if not self.is_running():
            self.log.info('not stopping container %s: '
                          'container is not running',
                          self.name)
            return

        self.log.info('stopping container %s',
                      self.name)
        idocker('stop', self.name)


class AtomicContainer(Container):
    def __init__(self, image, name=None, spc=False):
        self.image = Image(image)
        self.name = name or self.image.default_container_name()
        self.spc = spc

        super(AtomicContainer, self).__init__(self.name)

    def format(self, args):
        vars = {
            'name': self.name,
            'image': self.image.name,
            'image_id': self.image.id,
        }

        return args.format(**vars)

    def environ(self):
        return {
            'ATOMIC_CONFDIR': self.format('/etc/{name}'),
            'ATOMIC_LOGDIR': self.format('/var/log/{name}'),
            'ATOMIC_DATADIR': self.format('/var/lib/{name}'),
        }

    def persistent(self):
        return self.image.get_boolean_label(
            'io.projectatomic.atomic.persistent')

    def build_run_command(self, oneshot=False):
        cmdline = [docker_path, 'run']
        cmdline += common_run_args

        if self.persistent() and not oneshot:
            cmdline += persistent_run_args
        else:
            cmdline += interactive_run_args
            if sys.stdin.isatty():
                cmdline += ['-t']

        if self.spc:
            cmdline += spc_run_args

        cmdline.append('{image}')

        return ' '.join(cmdline)

    def get_run_command(self):
        if self.spc:
            cmdline = self.build_run_command()
        else:
            cmdline = self.image.labels.get(
                'io.projectatomic.atomic.run',
                self.build_run_command())

        return self.format(cmdline)

    def get_install_command(self):
        if self.spc:
            cmdline = self.build_run_command(oneshot=True)
        else:
            cmdline = self.image.labels.get(
                'io.projectatomic.atomic.install',
                self.build_run_command(oneshot=True))

        return self.format(cmdline)

    def run_with_environ(self, cmd):
        self.log.debug('running command: %s',
                       cmd)
        env = os.environ
        env.update(self.environ())

        subprocess.check_call(cmd,
                              env=env,
                              shell=True)

    def create_persistent_container(self):
        self.log.info('creating persistent container %s',
                      self.name)
        cmd = self.get_run_command()
        self.run_with_environ(cmd)

    def run(self, cmd=None):
        if self.persistent():
            if not self.exists():
                self.create_persistent_container()
            elif not self.is_running():
                self.start()

            if cmd:
                self.run_in_running_container(cmd)
        else:
            if self.exists():
                self.delete()
            self.run_in_new_container(cmd)

    def install(self):
        cmd = self.image.labels.get('io.projectatomic.atomic.install',
                                    '/atomic/install')

        self.run([cmd])

    def uninstall(self):
        cmd = self.image.labels.get('io.projectatomic.atomic.uninstall',
                                    '/atomic/uninstall')

        self.run([cmd])

    def run_in_running_container(self, cmd=None):
        if not cmd:
            raise ValueError('command cannot be null')

        cmd = ' '.join(cmd)
        self.log.info('running in %s: %s',
                      self.name,
                      cmd)

        cmdline = 'docker exec -i %s %s %s' % (
            '-t' if sys.stdin.isatty() else '',
            self.name,
            cmd)
        self.run_with_environ(cmdline)

    def run_in_new_container(self, cmd=None):
        cmd = ' '.join(cmd or self.image.command())
        self.log.info('running in %s: %s',
                      self.name,
                      cmd)

        runcmd = self.get_run_command()
        cmdline = '%s %s' % (
            runcmd, cmd)

        self.run_with_environ(cmdline)

    def stop(self):
        if not self.is_running():
            self.log.warn('cannot stop %s: '
                          'container is not running.',
                          self.name)
            return

        if not self.persistent():
            self.log.warn('cannot stop %s: '
                          'container is not persistent.',
                          self.name)
            return

        cmd = self.image.labels.get('io.projectatomic.atomic.stop')
        if cmd:
            self.run_in_running_container([cmd])

        super(AtomicContainer, self).stop()
