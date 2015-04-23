from __future__ import absolute_import

import logging
import textwrap
import atomic.dockerapi as api
from cliff.lister import Lister


class AtomicInfo(Lister):

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AtomicInfo, self).get_parser(prog_name)
        parser.add_argument('--extended', '-x',
                            action='store_true')
        parser.add_argument('image')
        return parser

    def take_action(self, args):
        image = api.Image(args.image)
        info = image.info()
        if args.extended:
            info.update(image.extra_info())
        return (('Name', 'Value'), (
            (k, textwrap.fill(v, width=60))
            for k, v in info.items()))
