from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier
from fossbot.bbot.memoize import memoize

from buildbot.steps.source import Git
from buildbot.steps.shell import Configure, Compile, Test, ShellCommand, SetProperty

import buildbot.process.properties
from buildbot import util
from collections import Callable

from buildbot.process.properties import WithProperties

class interpolated(object):
    def __init__(self, fn):
        self.fn = fn

    def __get__(self, obj, objtype):
        return objtype('%%(%s)s' % self.fn.__name__)
    
class Portable(WithProperties):
    def __init__(self, fmt, **kw):
        kw = kw.copy()
        kw.update(
            dict(
                [ (k, v.fn) for k,v in 
                  self.__class__.__dict__.iteritems()
                  if isinstance(v, interpolated) ]))

        WithProperties.__init__(self, fmt, **kw)

    @interpolated
    def get_toolset_environ(p):
        if p['os'].startswith('win'):
            m = re.match(r'vc([0-9]+)(?:\.([0-9]))?', p['cc'])
            if m:
                return r'${VS%s%sCOMNTOOLS}\vsvars32 && python -c "import os;print os.environ"' % (m.group(1), m.group(2) or '0')
            else:
                return 'rem'
        return 'true'

    @interpolated
    def make(p):
        return p['os'].startswith('win') and 'nmake' or 'make'

    @interpolated
    def make_continue_opt(p):
        return p['os'].startswith('win') and '/K' or '-k' 

    @interpolated
    def nil(p):
        return p['os'].startswith('win') and 'echo' or 'true'

    @interpolated
    def shell(p):
        return p['os'].startswith('win') and 'cmd' or 'sh'

    @interpolated
    def shell_cmd_opt(p):
        return p['os'].startswith('win') and '/c' or '-c'


class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.addSteps(
            Git('http://github.com/%s.git' % repo, workdir='source'),

            SetProperty(
                description = 'Toolset setup',
                command = [ Portable.shell, Portable.shell_cmd_opt, Portable.get_toolset_environ ],
                extract_fn=
                  lambda status,out,err: dict( tool_environ=eval(out.strip() or 'None') )),
            )

        self.test('Debug')
        self.test('Release')

        self.step(
            ShellCommand(
                env=WithProperties('%(tool_environ)s'),
                workdir='Release',
                command = [Portable.make, 'documentation', '-k'],
                description='Documentation'))

    def test(self, variant):
        self.addSteps(
            SetProperty(
                description = 'Variant setup',
                command = [Portable.nil],
                extract_fn=lambda status,out,err: { 
                    'variant':variant, 
                    'src': (variant == 'Debug' and '../source' or '../Debug/monolithic'),
                    }),

            Configure(
                env=WithProperties('%(environ)s'),
                workdir=variant,
                command = [
                    'cmake', '-DBOOST_UPDATE_SOURCE=1', '-DBOOST_DEBIAN_PACKAGES=1', 
                    '-DCMAKE_BUILD_TYPE='+variant, WithProperties('%(src)s') ] ),

            Compile(
                env=WithProperties('%(environ)s'),
                workdir=variant, 
                command = [ Portable.make, Portable.make_continue_opt ]),

            Test(
                env=WithProperties('%(environ)s'),
                workdir=variant, 
                command = [ Portable.make, Portable.make_continue_opt, 'test' ]),
            )


name = 'Boost.Defrag'
hub_repo = 'ryppl/' + name


include_properties=['os', 'cc']

repositories=[GitHub(hub_repo)]

build_procedures=[ DefragTests(hub_repo) ]

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

status=[
    IRC(host="irc.freenode.net", nick="rypbot",
        notify_events=transitions,
        channels=["#ryppl"]),

    MailNotifier(fromaddr="buildbot@boostpro.com",
                 extraRecipients=["el-get-devel@tapoueh.org"],
                 mode='problem')]
