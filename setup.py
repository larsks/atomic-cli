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
              'update = atomic.cmd.atomic_update:AtomicUpdate',
              'run = atomic.cmd.atomic_run:AtomicRun',
          ],
      }
      )
