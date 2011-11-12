from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier

from buildbot.steps.shell import ShellCommand
from buildbot.schedulers.filter import ChangeFilter

from buildbot import util

name = 'Boost.Modularize'

include_features=['modbot']

repositories = [
    GitHub('ryppl/boost-svn'),
    GitHub('ryppl/boost-modularize'),
    ]

build_procedures=[ 
    BuildProcedure('Modularize')
    .addSteps(*
        reduce( lambda x,y: x+y,
            [repo.steps(
                workdir=repo.name, 
                # alwaysUseLatest=True,
                name='Git(%s)' % repo.name,
                haltOnFailure=True
                ) 
          for repo in repositories])
        +
        [ShellCommand(
                command=['python', '-u', 'modularize.py', '--src=../boost-svn', '--dst=../boost', cmd],
                name='modularize(%s)' % cmd,
                workdir='boost-modularize',
                haltOnFailure=True
                )
         for cmd in ('setup', 'update', 'push')])
    ]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["ryppl-dev@googlegroups.com"],
                 mode='problem')]

def make_change_filter(project):
    return ChangeFilter(
        repository_fn=lambda url: any(r.match_url(url) for r in repositories),
        branch='master')
