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
            '-DBUILDSTEP='+step, cmake_toolchain_opt, 
            '-P', 'build.cmake']

class IntegrationTest(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Integration Test')

        self.addSteps(
            Git(repourl='git://github.com/%s.git' % repo, haltOnFailure=True),
            Configure(command=cmake('configure'), haltOnFailure=True, alwaysRun=True),
            Compile(command=cmake('build'), haltOnFailure=True, alwaysRun=True),
            Test(command=cmake('test'), haltOnFailure=True, alwaysRun=True),
            ShellCommand(command=cmake('package'), name='Package'))


name = 'Boost'
hub_repo = 'boost-lib/boost'

include_features=['os', 'cc']

repositories=[GitHub(hub_repo, protocol='https')]

build_procedures=[ IntegrationTest(hub_repo) ]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]
