#!/usr/bin/env python

# Author: Dan Walsh <dwalsh@redhat.com>
import os
from setuptools import setup, find_packages

setup(name="atomic",
      install_requires=open('requirements.txt').readlines(),
      packages=find_packages(),
      version="2.0",
      description="Atomic Management Tool",
      author="Lars Kellogg-Stedman",
      author_email="lars@redhat.com",
      entry_points={
          'console_scripts': [
              'atomic = atomic.main:main',
          ],
          'com.redhat.atomic': [
              'info = atomic.cmd.atomic_info:AtomicInfo',
              'version = atomic.cmd.atomic_version:AtomicVersion',
              'update = atomic.cmd.atomic_update:AtomicUpdate',
              'run = atomic.cmd.atomic_run:AtomicRun',
              'stop = atomic.cmd.atomic_stop:AtomicStop',
              'host = atomic.cmd.atomic_host:AtomicHost',
              'install = atomic.cmd.atomic_install:AtomicInstall',
              'uninstall = atomic.cmd.atomic_uninstall:AtomicUninstall',
              'status = atomic.cmd.atomic_status:AtomicStatus',
          ],
      }
      )
