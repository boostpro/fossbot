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

def toolchain(props):
    m = re.match(r'vc(([0-9]+)(?:\.([0-9]))?)', props.getProperty('cc',''))
    if m:
        return r'vs' + m.group(1)
    return ''
    
    
def cmake(step):
    return ['cmake', '-DBUILDSTEP='+step, WithProperties('-DTOOLCHAIN=%(tc)s', tc=toolchain), '-P', 'build.cmake']

class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.addSteps(
            Git(repourl='git://github.com/%s.git' % repo),
            ShellCommand(command=cmake('aggregate'), description='Collect Modules'),
            Configure(command=cmake('configure')),
            Compile(command=cmake('build')),
            Test(command=cmake('test')),
            ShellCommand(command=cmake('package'), description='Package'))


name = 'Boost.Defrag'
hub_repo = 'ryppl/' + name

include_features=['os', 'cc']

repositories=[GitHub(hub_repo)]

build_procedures=[ DefragTests(hub_repo) ]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]
