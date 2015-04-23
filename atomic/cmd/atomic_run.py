from __future__ import absolute_import

import argparse
import logging
import atomic.dockerapi as api
from cliff.command import Command


class AtomicRun(Command):

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicRun, self).get_parser(prog_name)
        parser.add_argument('--name', '-n')
        parser.add_argument('--spc', '-s',
                            action='store_true')
        parser.add_argument('image')
        parser.add_argument('command', nargs=argparse.REMAINDER)
        return parser

    def take_action(self, args):
        container = api.AtomicContainer(args.image,
                                        name=args.name,
                                        spc=args.spc)
        container.run(args.command)
