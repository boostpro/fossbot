# -*- python -*-
# ex: set syntax=python:

import bbot
from bbot.slave import Slave

BuildmasterConfig = bbot.master(
    title = 'BoostPro FOSSbot',
    titleURL = 'http://github.com/boostpro/fossbot',
    buildbotURL = 'http://bbot.boost-consulting.com',

    slaves = [
        Slave(
            'boostpro-win03-1',
            properties=dict(os='win32', cplusplus=True, emacs=True)),
        
        Slave(
            'boostpro-ubu11.04-1',
            properties=dict(os='linux', cplusplus=True, emacs=True)),
        ],

    projects = 'fossbot.projects'
    )


