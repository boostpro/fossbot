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


    name = "Boost.Defrag"

    def __init__(self):
        """
        """
        Source.__init__(self)
        self.addFactoryArguments(repourl=repourl,
                                 branch=branch,
                                 progress=progress,
                                 )
        self.args.update({'branch': branch,
                          'progress': progress,
                          })

    def startVC(self, branch, revision, patch):
        slavever = self.slaveVersion("mtn")
        if not slavever:
            raise BuildSlaveTooOldError("slave is too old, does not know "
                                        "about mtn")

        self.args['repourl'] = self.computeRepositoryURL(self.repourl)
        if branch:
            self.args['branch'] = branch
        self.args['revision'] = revision
        self.args['patch'] = patch

        cmd = LoggedRemoteCommand("mtn", self.args)
        self.startCommand(cmd)

    def computeSourceRevision(self, changes):
        if not changes:
            return None
        # without knowing the revision ancestry graph, we can't sort the
        # changes at all. So for now, assume they were given to us in sorted
        # order, and just pay attention to the last one. See ticket #103 for
        # more details.
        if len(changes) > 1:
            log.msg("Monotone.computeSourceRevision: warning: "
                    "there are %d changes here, assuming the last one is "
                    "the most recent" % len(changes))
        return changes[-1].revision

def cmake(step):
    return ['cmake', '-DBUILDSTEP='+step, '-P', 'build.cmake']

class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.addSteps(
            Git(repourl='git://github.com/%s.git' % repo),
            ShellCommand(command=cmake('aggregate'), description='Collect Modules'),
            Configure(command=cmake('configure')),
            Build(command=cmake('build')),
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
