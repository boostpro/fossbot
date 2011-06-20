import bbot
from bbot.slave import Slave
from bbot.status import GitHubWebStatus

from twisted.python import log
if 'BuildmasterConfig' in globals():
    log.msg('reloading '+__name__)

# Monkeypatch to work around http://trac.buildbot.net/ticket/1948
if 'real_compareToSetup' not in globals():
    from buildbot.process.builder import Builder
    real_compareToSetup = Builder.compareToSetup
    Builder.compareToSetup = lambda self, setup: real_compareToSetup(self,setup)+ ['forced update']

BuildmasterConfig = bbot.master(
    title = 'BoostPro FOSSbot',
    titleURL = 'http://github.com/boostpro/fossbot',
    buildbotURL = 'http://bbot.boostpro.com',

    slaves = [
        Slave(
            'boostpro-ubu11.04x64-2', max_builds=2,
            features=dict(os='linux', cc=['gcc'], emacs='23.3', modbot='x', architecture='x64')),

        Slave(
            'boostpro-win08x64-2', max_builds=2,
            features=dict(
                os='win64', 
                cc=['vc7.1', 'vc8', 'vc9', 'vc10'], 
                emacs='23.3', 
                )
            ),
        ],
        
    projects = 'fossbot.projects',
    status = [GitHubWebStatus(http_port='tcp:8010:interface=127.0.0.1')()],
    )

from pprint import pprint
pprint(BuildmasterConfig)
