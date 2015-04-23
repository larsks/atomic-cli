import sys
import logging

from cliff.app import App
from cliff.commandmanager import CommandManager

class Atomic (App):
    log = logging.getLogger(__name__)

    def __init__(self):
        super(Atomic, self).__init__(
            description='Atomic CLI',
            version='2',
            command_manager=CommandManager('com.redhat.atomic'),
        )

    def build_option_parser(self, *args, **kwargs):
        parser = super(Atomic, self).build_option_parser(*args, **kwargs)
        return parser

    def initialize_app(self, argv):
        pass

    def configure_logging(self):
        loglevel = {0: 'WARNING',
                    1: 'INFO',
                    2: 'DEBUG'}.get(self.options.verbose_level,
                                    logging.DEBUG)
        logging.basicConfig(
            level=loglevel)


app = Atomic()


def main():
    return app.run(sys.argv[1:])

if __name__ == '__main__':
    main()
