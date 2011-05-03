from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier
from fossbot.bbot.memoize import memoize

from buildbot.steps.source import Git
from buildbot.steps.shell import Configure, Compile, Test, ShellCommand, SetProperty

import buildbot.process.properties
from buildbot import util
from collections import Callable

class WithProperties(buildbot.process.properties.WithProperties):
    """
    This is a marker class, used fairly widely to indicate that we
    want to interpolate build properties.
    """

    compare_attrs = ('fmtstring', 'args', 'kw')

    def __init__(self, fmtstring, *args, **kw):
        self.fmtstring = fmtstring
        self.args = args
        self.kw = kw
        if args and kw:
            raise ValueError('WithProperties takes either positional or keyword substitutions, not both.')

    def __repr__(self):
        return self.__class__.__name__+'(%(fmtstring)r, *%(args)r, **%(kw)r)' % self.__dict__

    def render(self, pmap):
        if self.args:
            strings = []
            for name in self.args:
                strings.append(pmap[name])
            s = self.fmtstring % tuple(strings)
        else:
            for k,v in self.kw.iteritems():
                pmap.add_temporary_value(k, v)

            properties = pmap.properties()
            print '#######', 
            import pprint
            pprint.pprint(properties.asDict())
            for k,v in properties.asDict().iteritems():
                if isinstance(v, Callable):
                    pmap.add_temporary_value(k, v(properties))
            s = self.fmtstring % pmap
            pmap.clear_temporary_values()
        return s

def toolchain_setup(p):
    if p['os'].startswith('win'):
        m = re.match(r'vc([0-9]+)(?:\.([0-9]))?', p['cc'])
        if m:
            return r'${VS%s%sCOMNTOOLS}\vsvars32' % (m.group(1), m.group(2) or '0')
        else:
            return 'title'
    return 'true'

portability_properties = dict(
    make=lambda p: p['os'].startswith('win') and 'nmake' or 'make',
    make_k=lambda p: p['os'].startswith('win') and '-k' or '/K',
    toolchain_setup=toolchain_setup,
    )

def variant_properties(variant):
    return dict(
        src=lambda _:'variant'=='Debug' and '../source' or '../debug/monolithic',
        variant=variant)

def propertize(stepClass, properties):
    class Propertized(stepClass):
        __properties=properties
        
        def start(self):
            for k,v in self.__properties.iteritems():
                # Allow property values from earlier to be used here
                # but don't overwrite any rendered stuff
                if not isinstance(v, Callable):
                    self.setProperty(k, v)
            self.setCommand
            return stepClass.start(self)

    return Propertized
            
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
        props = variant_properties(variant)
        props.update(portability_properties)

        self.addSteps(
            SetProperty(command = ['echo'], extract_fn=lambda status,out,err: props),

            Configure(
                command = [ 'cmake', '-DBOOST_UPDATE_SOURCE=1',
                            '-DBOOST_DEBIAN_PACKAGES=1', 
                            WithProperties('-DCMAKE_BUILD_TYPE=%(variant)s') ] ),

            Compile(command = [ WithProperties('%(make)s'), WithProperties('%(make_k)s') ]),
            Test(command = [ WithProperties('%(make)s'), WithProperties('%(make_k)s'), 'test' ]),
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
