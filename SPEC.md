# Atomic Container Specification

This is a specification for images designed to operate cleanly with
the `atomic` command line utility.

## Labels

The `atomic` command makes use of certain labels (created with the
`LABEL` command in your `Dockerfile`) to control its behavior:

- `io.projectatomic.atomic.run` -- This is the complete Docker command
  line used to start a container from the image.  This should only be
  used in exceptional cases; otherwise, images should be designed to
  work with the default command line invocations detailed below.

- `io.projectatomic.atomic.start` -- This is a command run *inside* a
  persistent container after it is started and before processing any
  user-provided command.

- `io.projectatomic.atomic.install` -- This is a command that will be
  run *inside* a container in response to the `atomic install`
  command.  If this label is not specified, the `atomic install`
  command will run `/atomic/install`.

- `io.projectatomic.atomic.uninstall` -- This is a command that will be
  run *inside* a container in response to the `atomic uninstall`
  command.  If this label is not specified, the `atomic uninstall`
  command will run `/atomic/uninstall`.

- `io.projectatomic.atomic.stop` -- This is a command that will be run
  *inside* a persistent container in response to the `atomic stop`
  command.

- `io.projectatomic.atomic.persistent` -- This is a boolean value that
  determines whether or not to create a persistent container from the
  image.  See "Persistent vs. Interactive containers" below for details.

## Persistent vs. Interactive containers

By default, `atomic` assumes that a container will only exist for the
duration of a single interactive command.  For example, if you run...

    atomic run --spc larsks/atomic-interactive ps -fe

...then `atomic` will start a Docker container with a command line
similar to `docker run -t -i --rm larsks/atomic-interactive ps -fe`.
The container will start, execute the command, exit, and get removed
by the `docker` client.

If you set:

    LABEL io.projectatomic.atomic.persistent=true

Then the same `atomic run` invocation will instead start a container
in the background using `docker run -d ...`, and then will run `ps
-fe` inside the container using `docker exec`.  The container will
persist in the background until it exits or is explicitly stopped.

### Docker invocation for normal containers

When you use `atomic run` to start a container, that will by default
result in the following invocation for an interactive image (an image
that does not have `LABEL io.projectatomic.atomic.persistent=true`:

    docker run -t -i --rm \
      --name {name} \
      -v /etc/localtime:/etc/localtime \
      -e ATOMC_IMAGE={image} \
      -e ATOMIC_NAME={name} \
      {image} <command>

An image may override this behavior by providing an alternative
invocation in the `io.projectatomic.atomic.run` label.  The `atomic`
script will always append `<command>` to the command line, which will
be either a command passed on the `atomic` command line or the value
of the `CMD` field embedded in the image.

The `-t` argument is only provided to `docker` if *stdin* is a tty.

### Docker invocation for persistent containers

    docker run \
      --name {name} \
      -v /etc/localtime:/etc/localtime \
      -e ATOMC_IMAGE={image} \
      -e ATOMIC_NAME={name} \
      -d \
      {image}

### Docker invocation for super-privileged containers (SPC)

In addition to the arguments shown in the above examples, an SPC
(either interactive or persistent) will also receive:

    --privileged \
      -v /:/host \
      -v /run:/run \
      --net=host \
      --ipc=host \
      --pid=host \
      -e ATOMIC_SPC=1 \

## Installing and uninstalling a container

Some containers may need to make configuration changes on the host
in order to to be effective.  The `atomic install` command instructs a
container to perform the necessary configuration.  This will perform
the equivalent of:

    atomic run <image> /atomic/install

You can use the `io.projectatomic.atomic.install` label to specify a
command to run inside the container other than `/atomic/uninstall`.

The `atomic uninstall` command will run `/atomic/uninstall` inside the
container (or the value of `io.projectatomic.atomic.uninstall`) before
removing the container.
