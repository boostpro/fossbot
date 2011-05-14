from buildbot.steps.source import Git
from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier
from fossbot.bbot.memoize import memoize

from buildbot.steps.source import Source
from buildbot.steps.shell import Configure, Compile, Test, ShellCommand, SetProperty
from buildbot.process.properties import WithProperties

import buildbot.process.properties
from buildbot import util
from collections import Callable
import re

from twisted.python import log

msvc = re.compile(r'vc([0-9]+)(?:\.([0-9]))?')

def cmake_toolchain(props):
    m = re.match(r'vc(([0-9]+)(?:\.([0-9]))?)', props.getProperty('cc',''))
    if m:
        return r'vs' + m.group(1)
    return ''
cmake_toolchain_opt = WithProperties('-DTOOLCHAIN=%(tc)s', tc=cmake_toolchain)

def on_windows(props):    
    return props.getProperty('os','').startswith('win')

cmake_continue_opt = WithProperties(
    '%(x)s',x=lambda p: on_windows(p) and '/K' or '-k')

def cmake(step):
    return ['cmake', cmake_continue_opt, 
            '-DBUILDDIR=../build',
            '-DBUILDSTEP='+step, cmake_toolchain_opt, 
            '-P', 'build.cmake']


name = 'Boost'
hub_repo = 'boost-lib/boost'

include_features=['os', 'cc']

repositories=[GitHub(hub_repo, protocol='https')]

build_procedures=[ 
    BuildProcedure('Integration')
    .addSteps(
        repositories[0].step(workdir='boost', haltOnFailure=True),
        Configure(workdir='boost', command=cmake('configure'), haltOnFailure=True, alwaysRun=True),
        Compile(workdir='boost', command=cmake('build'), haltOnFailure=True, alwaysRun=True),
        Test(workdir='boost', command=cmake('test'), haltOnFailure=True, alwaysRun=True),
        ShellCommand(workdir='boost', command=cmake('package'), name='Package'))
]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]
