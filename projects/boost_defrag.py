from fossbot.bbot.repository import GitHub
from fossbot.bbot.procedures import BuildProcedure
from fossbot.bbot.status import IRC, MailNotifier

from buildbot.steps.source import Git
from buildbot.steps.shell import Configure, Compile, Test, ShellCommand

class Variant(object):
    def __init__(self, name):
        self.name = name

    def __call__(self, klass, **kw):
        desc = kw.pop('description', klass.__name__)
        return klass(
            description = self.name + ' ' + desc,
            workdir = self.name.lower(),
            **kw)

class MakeMixin(object):
    @property
    def make(self):
        if 'win' in self.getProperty('os'):
            return 'nmake'
        else:
            return 'make'

    @property
    def makeopt(self):
        if 'win' in self.getProperty('os'):
            return '/K'
        else:
            return '-k'

class Make(Compile, MakeMixin):
    def start(self):
        self.setCommand([self.make, self.makeopt])

class MakeTest(Test, MakeMixin):
    def start(self):
        self.setCommand([self.make, self.makeopt, 'test'])

class DefragTests(BuildProcedure):
    def __init__(self, repo):
        BuildProcedure.__init__(self, 'Boost.Defrag')

        self.addStep(
            Git('http://github.com/%s.git' % repo, workdir='source'))

        self.test(Variant('Debug'))

        self.test(Variant('Release'))

        self.addStep(
            ShellCommand(
                description='Documentation',
                command = ['make', 'documentation', '-k'],
                workdir = 'release'))

    def test(self, variant):
        src_dirs = {'Debug' : '../source', 'Release' : '../debug/monolithic'}
        src_dir = src_dirs[variant.name]

        self.addSteps(
            variant(
                Configure,
                command = [ "cmake", "-DBOOST_UPDATE_SOURCE=1",
                            "-DBOOST_DEBIAN_PACKAGES=1", "-DCMAKE_BUILD_TYPE=Debug", src_dir ]
                ),
            variant(Make),
            variant(MakeTest))


hub_repo = 'ryppl/Boost.Defrag'
name = 'Boost.Defrag'


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
