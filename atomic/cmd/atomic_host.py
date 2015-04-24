from __future__ import absolute_import

import logging
import subprocess
import argparse
from cliff.command import Command


class AtomicHost(Command):
    '''Run rpm-ostree commands.'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicHost, self).get_parser(prog_name)
        parser.add_argument('hostargs', nargs=argparse.REMAINDER)
        return parser

    def take_action(self, args):
        subprocess.check_call(['rpm-ostree'] + list(args.hostargs))
