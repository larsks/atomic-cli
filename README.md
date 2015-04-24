# WARNING PROTOTYPE STAY AWAY

This is a prototype of the `atomic` command line tool for managing
Docker containers, particularly those that are meant to integrate in
some way with the host.

## Synopsis

    usage: atomic [--version] [-v] [--log-file LOG_FILE] [-q] [-h] [--debug]
           <command> [...]

    Atomic CLI

    optional arguments:
      --version            show program's version number and exit
      -v, --verbose        Increase verbosity of output. Can be repeated.
      --log-file LOG_FILE  Specify a file to log output. Disabled by default.
      -q, --quiet          suppress output except warnings and errors
      -h, --help           show this help message and exit
      --debug              show tracebacks on errors

## Commands

- `complete` -- print bash completion command
- `help` -- print detailed help for another command
- `host` -- Run rpm-ostree commands.
- `info` -- Return metadata about an image.
- `install` -- Install an Atomic container.
- `run` -- Run a command inside a container.
- `status` -- Return status of an atomic container.
- `stop` -- Stop a command inside a container.
- `uninstall` -- Uninstall an atomic container.
- `update` -- Ensure you have the latest version of an image.
- `version` -- Return the Name-Version-Release string for an image.

## An example interactive SPC

We would like to run the `tcpdump` command, which is not available on
our host but is available in the `larsks/atomic-interactive` image:

    # atomic run --spc larsks/atomic-interactive tcpdump -i enp0s25 -n
    INFO:atomic.dockerapi:running in atomic-interactive-spc: tcpdump -i enp0s25 -n
    tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
    listening on enp0s25, link-type EN10MB (Ethernet), capture size 262144 bytes
    14:23:36.407156 STP 802.1d, Config, Flags [none], bridge-id ffff.ff:ff:90:86:6f:72.8003, length 43

## An example persisent SPC

In this example, we set up `larsks/atomic-persisent` as a persistent
super-privileged container.

Install the `larsks/atomic-persistent` container:

    # atomic install --spc larsks/atomic-persistent

This starts a simple webserver on port 80 and registers a cron job in `/etc/cron.d/update-time`.  Once started, we can see the status of the container with the `status` command:

    # atomic status --spc larsks/atomic-persistent
    +---------+--------------------------+
    | Field   | Value                    |
    +---------+--------------------------+
    | Image   | larsks/atomic-persistent |
    | Exists  | True                     |
    | Running | True                     |
    | PID     | 14403                    |
    | Address |                          |
    +---------+--------------------------+

The `Address` field is blank here because we are running an SPC, which
uses the host's network namespace.  We can also use the `atomic run`
command to run a command inside the container:

    # atomic run --spc larsks/atomic-persistent \
      cat /content/last-updated.txt
    INFO:atomic.dockerapi:running in atomic-persistent-spc: cat /content/last-updated.txt
    Fri Apr 24 14:16:01 EDT 2015
    
The `atomic uninstall` command will remove the cron job installed by
`atomic install` and will delete the container:

    # atomic uninstall --spc larsks/atomic-persistent
    INFO:atomic.dockerapi:running in atomic-persistent-spc: /atomic/uninstall
    INFO:atomic.dockerapi:deleting container atomic-persistent-spc
    a0899a1befc850f75b6de199fcee3aced6d74cacf02ee16f44617c0657362368

## Output options

Because this application is implemented using [cliff][], commands that
produce tabular output can be filtered in various ways.  For example,
the `info` command will by default produce a nicely formatted table:

[cliff]: https://pypi.python.org/pypi/cliff

    $ atomic info rhel7/rhel-tools
    +--------------+------------------------------------+
    | Field        | Value                              |
    +--------------+------------------------------------+
    | Architecture | x86_64                             |
    | Build_Host   | rcm-img03.build.eng.bos.redhat.com |
    | Name         | rhel-tools-docker                  |
    | Release      | 9                                  |
    | Vendor       | Red Hat, Inc.                      |
    | Version      | 7.1                                |
    +--------------+------------------------------------+

We can instead extract the data as a series of shell-style
"name=value" expressions:

    $ atomic info rhel7/rhel-tools -f shell
    architecture="x86_64"
    build_host="rcm-img03.build.eng.bos.redhat.com"
    name="rhel-tools-docker"
    release="9"
    vendor="Red Hat, Inc."
    version="7.1"

We can also limit the output to a single attribute:

    
    $ atomic info rhel7/rhel-tools -f value -c Vendor
    Red Hat, Inc.

These formatting options can be used with the `info` and `status`
subcommands.
