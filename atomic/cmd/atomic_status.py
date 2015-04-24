from __future__ import absolute_import

import logging
import textwrap
import atomic.dockerapi as api
from cliff.show import ShowOne


class AtomicStatus(ShowOne):
    '''Return status of an atomic container.'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicStatus, self).get_parser(prog_name)
        parser.add_argument('--spc', '-s',
                            action='store_true')
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        container = api.AtomicContainer(args.image,
                                        spc=args.spc)

        return [
            ('Image', 'Exists', 'Running', 'PID', 'Address'),
            (container.image.name,
             container.exists(),
             container.is_running(),
             container.pid,
             container.address,
             )
        ]
