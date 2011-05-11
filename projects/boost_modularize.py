from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier

from buildbot.steps.shell import ShellCommand

from buildbot import util

name = 'Boost.Modularize'

include_features=['modbot']

repositories=[GitHub('boost-lib/boost-supermodule', protocol='ssh'),
              GitHub('ryppl/boost-svn'),
              GitHub('boost-lib/boost-modularize'),
              ]

build_procedures=[ 
    BuildProcedure('Modularize')
    .addSteps(
        *[repo.step() for repo in repositories]
         + [ShellCommand(
                command=['python', 'modularize.py', '--src=../boost-svn', '--dst=../boost-supermodule>', cmd],
                description=cmd)
            for cmd in ('update', 'push')])
    ]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]


