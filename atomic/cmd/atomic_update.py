from __future__ import absolute_import

import logging
import atomic.dockerapi as api
from atomic.exceptions import AtomicError
from cliff.command import Command


class AtomicUpdate(Command):

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicUpdate, self).get_parser(prog_name)
        parser.add_argument('--force', '-f',
                            action='store_true')
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        image = api.Image(args.image)
        if not image.exists():
            raise AtomicError('Image %s does not exist' % image.name)
        image.update_image(force=args.force)
