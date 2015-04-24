from __future__ import absolute_import

import logging
import textwrap
import atomic.dockerapi as api
from cliff.command import Command


class AtomicVersion(Command):
    '''Return the Name-Version-Release string for an image.'''

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicVersion, self).get_parser(prog_name)
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        image = api.Image(args.image)
        print ('-'.join(image.version()))
