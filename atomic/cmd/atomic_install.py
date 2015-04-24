from __future__ import absolute_import

import logging
import atomic.dockerapi as api
from cliff.command import Command


class AtomicInstall(Command):
    '''Install an Atomic container.'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicInstall, self).get_parser(prog_name)
        parser.add_argument('--name', '-n')
        parser.add_argument('--replace', '-r',
                            action='store_true')
        parser.add_argument('--spc', '-s',
                            action='store_true')
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        container = api.AtomicContainer(args.image,
                                        name=args.name,
                                        spc=args.spc)
        if args.replace and container.exists():
            container.delete(force=True)
        container.install()
