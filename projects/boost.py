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

def cmake_generator(build):
    cc = build.getProperties().getProperty('cc','')
    if (cc == "vc10"):
        return "Visual Studio 10"
    elif (cc == "vc9"):
        return "Visual Studio 9 2008"
    elif (cc == "vc8"):
        return "Visual Studio 8 2005"
    elif (cc == "vc7.1"):
        return "Visual Studio 7 .NET 2003"
    return "Unix Makefiles"

def cmake(step):
    return ['cmake',
            '-DBUILDDIR=../build',
            WithProperties('-DBUILDSTEP='+step),
            WithProperties('-DGENERATOR=%(gen)s', gen=cmake_generator), 
            '-P', 'build.cmake']


class CMakeBuild(Compile):

    def __init__(self, config, target = None, **kwargs):
        self.config = config
        self.target = target
        Compile.__init__(self, **kwargs)

    def start(self):
        multi = self.getProperties().getProperty('cc','').startswith("vc")
        command = ["cmake", "--build", "." if multi else self.config]
        if multi:
            command.append("--config")
            command.append(self.config)
        if self.target is not None:
            command.append("--target")
            command.append(self.target)
        self.setCommand(command)
        return Compile.start(self)


name = 'Boost'
hub_repo = 'ryppl/boost-zero'

include_features=['os', 'cc']

repositories=[GitHub(hub_repo, protocol='https')]

build_procedures=[
    BuildProcedure('Integration').addSteps(
        *repositories[0].steps(workdir='boost', haltOnFailure=True))
    .addSteps(
        Configure(workdir='boost', command=cmake('%(clean:+clean)sconfigure'), haltOnFailure=True),
        CMakeBuild('Debug', workdir='boost/build', haltOnFailure=False),
        CMakeBuild('Release', workdir='boost/build', haltOnFailure=False),
        Test(workdir='boost', command=cmake('test'), haltOnFailure=False),
        ShellCommand(workdir='boost', command=cmake('documentation'), name='Docs')
        )
]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]
