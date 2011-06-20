from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier

from buildbot.steps.shell import ShellCommand

from buildbot import util

name = 'Boost.Modularize'

include_features=['modbot']

repositories=[GitHub('boost-lib/boost', protocol='ssh'),
              GitHub('ryppl/boost-svn'),
              GitHub('ryppl/boost-modularize'),
              ]

build_procedures=[ 
    BuildProcedure('Modularize')
    .addSteps(*
        [repo.step(
                workdir=repo.name, 
                # alwaysUseLatest=True,
                name='Git(%s)' % repo.name,
                haltOnFailure=True
                ) 
          for repo in repositories]
        +
        [ShellCommand(
                command=['python', 'modularize.py', '--src=../boost-svn', '--dst=../boost', cmd],
                name='modularize(%s)' % cmd,
                workdir='boost-modularize',
                haltOnFailure=True
                )
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


