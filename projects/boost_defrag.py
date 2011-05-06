from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier
from fossbot.bbot.memoize import memoize

from buildbot.steps.source import Git
from buildbot.steps.shell import Configure, Compile, Test, ShellCommand, SetProperty
from buildbot.process.properties import WithProperties

import buildbot.process.properties
from buildbot import util
from collections import Callable
import re

from twisted.python import log
if 'Portable' in globals():
    log.msg('reloading '+__name__)

class Portable(WithProperties):
    def __init__(self, fmt, **kw):
        kw = kw.copy()

        for name in re.findall(r'(?<!%)%[(]([A-Za-z_]\w*)[)]', fmt):
            f = self.__class__.__dict__.get(name, None)
            if f: kw[name] = f

        WithProperties.__init__(self, fmt, **kw)

    def tool_path(p):
        m = re.match(r'vc([0-9]+)(?:\.([0-9]))?', p['cc'])
        if m:
            return r'${VS%s%sCOMNTOOLS};${PATH}' % (m.group(1), m.group(2) or '0')
        return '${PATH}'

    def tool_setup(p):
        m = re.match(r'vc([0-9]+)(?:\.([0-9]))?', p['cc'])
        if m:
            return r'vsvars32.bat &&'
        return ''

    def make(p):
        return p['os'].startswith('win') and 'nmake' or 'make'

    def make_continue_opt(p):
        return p['os'].startswith('win') and '/K' or '-k' 

    def nil(p):
        return p['os'].startswith('win') and 'rem' or 'true'

    def shell(p):
        return p['os'].startswith('win') and 'cmd' or 'sh'

    def shell_cmd_opt(p):
        return p['os'].startswith('win') and '/c' or '-c'

    def slash(p):
        return p['os'].startswith('win') and '\\' or '/'


class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.test('Debug')
        self.test('Release')

        self.step(
            ShellCommand(
                workdir='Release',
                env=dict(PATH=Portable('%(tool_path)s')),
                command = Portable('%(tool_setup)s %(make)s %(make_continue_opt)s documentation'),
                description='Documentation'))

    def test(self, variant):
        srcdir = (variant == 'Debug' and '..%(slash)ssource' or '..%(slash)sDebug%(slash)smonolithic')

        self.addSteps(
            Configure(
                workdir=variant,
                env=dict(PATH=Portable('%(tool_path)s')),
                command = Portable(
                    '%(tool_setup)s cmake -DBOOST_UPDATE_SOURCE=1'
                    ' -DBOOST_DEBIAN_PACKAGES=1 -DCMAKE_BUILD_TYPE='+variant+' '
                    + srcdir)),

            Compile(
                workdir=variant, 
                env=dict(PATH=Portable('%(tool_path)s')),
                command = Portable('%(tool_setup)s %(make)s %(.make_continue_opt)s')),

            Test(
                workdir=variant, 
                env=dict(PATH=Portable('%(tool_path)s')),
                command = Portable('%(tool_setup)s %(make)s %(.make_continue_opt)s test ')))


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
