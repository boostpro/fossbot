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
        kw.update(self.__class__.__dict__)
        WithProperties.__init__(self, fmt, kw)

    @interpolated
    def setup(p):
        if p['os'].startswith('win'):
            m = re.match(r'vc([0-9]+)(?:\.([0-9]))?', p['cc'])
            if m:
                return r'${VS%s%sCOMNTOOLS}\vsvars32' % (m.group(1), m.group(2) or '0')
            else:
                return 'title'
        return 'true'

    @interpolated
    def make(p):
        return p['os'].startswith('win') and 'nmake' or 'make'

    @interpolated
    def make_continue_opt(p):
        return p['os'].startswith('win') and '-k' or '/K'

    @interpolated
    def nil(p):
        return p['os'].startswith('win') and 'echo' or 'true'

def variant_properties(variant):
    return dict(
        src=lambda _:'variant'=='Debug' and '../source' or '../debug/monolithic',
        variant=variant)
            
class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.addStep(
            Git('http://github.com/%s.git' % repo, workdir='source'))

        self.test('Debug')
        self.test('Release')

        self.step(
            ShellCommand(
                command = ['make', 'documentation', '-k'],
                description='Documentation'))

    def test(self, variant):
        setup = [ Portable.setup, '&&' ]

        self.addSteps(
            SetProperty(
                command = [Portable.nil],
                extract_fn=lambda status,out,err: { 
                    'variant':variant, 
                    'src': (variant == 'Debug' and '../source' or '../debug/monolithic'),
                    }),

            Configure(
                command = setup + [
                    'cmake', '-DBOOST_UPDATE_SOURCE=1', '-DBOOST_DEBIAN_PACKAGES=1', 
                    '-DCMAKE_BUILD_TYPE='+variant, WithProperties('%(src)s') ] ),

            Compile(command = setup + [ Portable.make, Portable.make_continue_opt ]),
            Test(command = setup + [ Portable.make, Portable.make_continue_opt, 'test' ]),
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
