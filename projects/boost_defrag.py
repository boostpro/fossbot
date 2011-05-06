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

msvc = re.compile(r'vc([0-9]+)(?:\.([0-9]))?')

class Portable(WithProperties):

    class word(object):
        def __init__(self, fn):
            self.fn = fn

        def __get__(self, obj, objtype):
            return objtype('%%(%s)s' % self.fn.__name__)

    def __init__(self, fmt, **kw):
        kw = kw.copy()

        for name in re.findall(r'(?<!%)%[(]([A-Za-z_]\w*)[)]', fmt):
            f = self.__class__.__dict__.get(name, None)
            if isinstance(f, Portable.word): f=f.fn
            if f: kw[name] = f

        WithProperties.__init__(self, fmt, **kw)

    @word
    def tool_path(p):
        m = msvc.match(p['cc'])
        if m:
            return r'${VS%s%sCOMNTOOLS};${PATH}' % (m.group(1), m.group(2) or '0')
        return '${PATH}'

    @word
    def tool_setup(p):
        m = msvc.match(p['cc'])
        if m:
            return r'vsvars32.bat'
        return ''

    @word
    def make(p):
        return p['os'].startswith('win') and 'nmake' or 'make'

    @word
    def make_continue_opt(p):
        return p['os'].startswith('win') and '/K' or '-k' 

    @word
    def nil(p):
        return p['os'].startswith('win') and 'rem' or 'true'

    @word
    def shell(p):
        return p['os'].startswith('win') and 'cmd' or 'sh'

    @word
    def shell_cmd_opt(p):
        return p['os'].startswith('win') and '/c' or '-c'

    def slash(p):
        return p['os'].startswith('win') and '\\' or '/'


class CMake(Configure):
    def start(self):
        cc = self.build.getProperties().getProperty('cc', '')
        if msvc.match(cc):
            self.setCommand([Portable.tool_setup, '&&', 'cmake', '-GNMake Makefiles'] + self.command)
        else:
            self.setCommand(['cmake'] + self.command)
        Configure.start(self)

class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.test('Debug')
        self.test('Release')

        _ = Portable
        self.step(
            ShellCommand(
                workdir='Release',
                env=dict(PATH=_.tool_path),
                command = [_.make, _.make_continue_opt, 'documentation'],
                description='Documentation'))

    def test(self, variant):
        _ = Portable
        srcdir = _(variant == 'Debug' and '..%(slash)ssource' 
                   or '..%(slash)sDebug%(slash)smonolithic')

        self.addSteps(
            CMake(
                workdir=variant,
                env=dict(PATH=_.tool_path),
                command = [
                    '-DBOOST_UPDATE_SOURCE=1',
                    ' -DBOOST_DEBIAN_PACKAGES=1', '-DCMAKE_BUILD_TYPE='+variant,
                    srcdir]),
            Compile(
                workdir=variant, 
                env=dict(PATH=_.tool_path),
                command = [_.make, _.make_continue_opt]),
            Test(
                workdir=variant, 
                env=dict(PATH=_.tool_path),
                command = [_.make, _.make_continue_opt, 'test']),
            )


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
