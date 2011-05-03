import bbot
from bbot.slave import Slave
from bbot.status import GitHubWebStatus

BuildmasterConfig = bbot.master(
    title = 'BoostPro FOSSbot',
    titleURL = 'http://github.com/boostpro/fossbot',
    buildbotURL = 'http://bbot.boost-consulting.com',

    slaves = [
        Slave(
            'boostpro-win03-1',
            properties=dict(os='win32', cc=['vc7.1', 'vc8', 'vc9', 'vc10'], emacs=True)),
        
        Slave(
            'boostpro-ubu11.04-1',
            properties=dict(os='linux', cc=['gcc'], emacs=True)),
        ],

    projects = 'fossbot.projects',
    status = [GitHubWebStatus(http_port='tcp:8010:interface=127.0.0.1')()],
    )
