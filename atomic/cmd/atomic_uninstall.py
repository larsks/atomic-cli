from __future__ import absolute_import

import logging
import atomic.dockerapi as api
from atomic.exceptions import AtomicError
from cliff.command import Command


class AtomicUninstall(Command):
    '''Uninstall an atomic container.'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicUninstall, self).get_parser(prog_name)
        parser.add_argument('--name', '-n')
        parser.add_argument('--keep', '-k',
                            action='store_true')
        parser.add_argument('--spc', '-s',
                            action='store_true')
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        container = api.AtomicContainer(args.image,
                                        name=args.name,
                                        spc=args.spc)
        if not container.exists():
            raise AtomicError('container %s does not exist and cannot be '
                              'uninstalled.' % container.name)

        container.uninstall()
        if not args.keep:
            container.delete(force=True)
