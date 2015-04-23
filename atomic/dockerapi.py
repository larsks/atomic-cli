from __future__ import absolute_import

import logging
import json
import subprocess
import shlex
from decorator import decorator


docker_path = '/usr/bin/docker'
default_cmd = ['/bin/sh']

spc_run_command = [
    'docker', 'run',
    '-t',
    '-i',
    '--rm',
    '--privileged',
    '-v', '/:/host',
    '-v', '/run:/run',
    '-v', '/etc/localtime:/etc/localtime',
    '--net=host',
    '--ipc=host',
    '--pid=host',
    '--name', '{name}',
    '-e', 'HOST=/host',
    '-e', 'NAME={name}',
    '-e', 'IMAGE={image}',
    '{image}',
]

default_run_command = [
    'docker', 'run',
    '--name', '{name}',
    '-e', 'IMAGE={image}',
    '-e', 'NAME={name}',
    '-t',
    '-i',
    '--name', '{name}',
    '{image}',
]


def idocker(*args):
    cmd = [docker_path]
    subprocess.check_call(cmd + list(args))


def docker(*args):
    cmd = [docker_path]
    stdout = subprocess.check_output(cmd + list(args))
    return stdout


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

    @property
    def id(self):
        return self.get('Id')


@decorator
def pim(func, self, *args, **kw):
    self.pull_if_missing()
    return func(self, *args, **kw)


class Image (Inspectable):
    def default_container_name(self):
        name = self.name.split('/')[-1].split(':')[0]
        return name

    def pull(self):
        self.log.info('pulling image %s', self.name)
        idocker('pull', self.name)
        self.refresh()

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

    def get_list_label(self, label):
        return shlex.split(self.labels.get(label, ''))

    def get_boolean_label(self, label):
        return (self.labels.get(label, 'false').lower()
                in ['true', 'yes'])

    @pim
    def info(self):
        basic = dict((k, v) for k, v in self.labels.items()
                     if ':' not in k and not k.isupper())
        return basic

    @pim
    def extra_info(self):
        special = dict((k, v) for k, v in self.labels.items()
                       if ':' in k or k.isupper())

        return special


class Container (Inspectable):
    def is_running(self):
        return self.exists() and self['State']['Running']

    def is_interactive(self):
        return self.exists() and all((self['Config'][opt] is True
                                      for opt in ['AttachStdin',
                                                  'AttachStdout',
                                                  'AttachStderr']))

    def delete(self, force=False):
        cmd = ['rm']
        if force:
            cmd.append('--force')
        cmd.append(self.id)
        docker(*cmd)


class AtomicContainer(Container):
    def __init__(self, image, name=None, spc=False):
        self.image = Image(image)
        self.name = name or self.image.default_container_name()
        self.spc = spc
        if self.spc:
            self.name += '-spc'

        super(AtomicContainer, self).__init__(self.name)

    def format_arg(self, arg):
        vars = {
            'name': self.name,
            'image': self.image.name,
        }

        return arg.format(**vars)

    def format_args(self, args):
        return [self.format_arg(arg) for arg in args]

    def environ(self):
        return {
            'CONFDIR': self.format_arg('/etc/{name}'),
            'LOGDIR': self.format_arg('/var/log/{name}'),
            'DATADIR': self.format_arg('/var/lib/{name}'),
        }

    def start(self):
        pass

    def stop(self):
        pass

    def remove(self):
        pass

    def get_run_command(self):
        runcmd = None

        if self.spc:
            runcmd = spc_run_command
        if not runcmd:
            runcmd = self.image.get_list_label('atomic:run')
        if not runcmd:
            runcmd = default_run_command

        return self.format_args(runcmd)

    def get_install_command(self):
        installcmd = self.image.get_list_label('atomic:install')
        return installcmd

    def run(self, cmd=None):
        if self.is_running():
            self.run_in_running_container(cmd)
        elif self.exists():
            self.run_in_stopped_container(cmd)
        else:
            self.run_in_new_container(cmd)

    def run_in_running_container(self, cmd=None):
        pass

    def run_in_stopped_container(self, cmd=None):
        pass

    def run_in_new_container(self, cmd=None):
        pass

    def install(self):
        if not self.image.exists():
            self.image.pull()

        runcmd = self.get_install_cmd()
        self.log.info('installing container %s',
                      self.name)

    def uninstall(self):
        pass

    def version(self):
        info = self.image.info()
        info['Name'] = self.name
        try:
            return '{Name}-{Version}-{Release}'.format(**info)
        except KeyError:
            pass
