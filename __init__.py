# -*- python -*-
# ex: set syntax=python:

from bbot.procedures import GitHubElisp
from bbot.project import Project
from bbot.status import IRC, GitHubWebStatus, MailNotifier
from bbot.repository import GitHub
from bbot.slave import Slave

import bbot

transitions={'successToFailure' : 1,'failureToSuccess' : 1, 'exception':1}

BuildmasterConfig = bbot.master(
    name = 'BoostPro FOSSbot',
    name_url = 'http://github.com/boostpro/fossbot',
    bot_url = 'http://bbot.boostpro.com/',

    slaves = [
        Slave(
            'boostpro-win03-1',
            properties=dict(os='win32', emacs=True)),
        
        Slave(
            'boostpro-ubu11.04-1',
            properties=dict(os='linux', emacs=True)),
        ],

    projects = [
        Project('el-get', repositories=[GitHub('dimitri/el-get'), GitHub('dabrahams/el-get')], 
            include_properties=['emacs'],
            build_procedures=[GitHubElisp('dimitri/el-get')], 
            status=[
                IRC(host="irc.freenode.net", nick="elgetbot",
                    notify_events=transitions,
                    channels=["#el-get"]),

                GitHubWebStatus('dimitri/el-get', http_port='tcp:8010:interface=127.0.0.1'),

                MailNotifier(fromaddr="buildbot@boostpro.com",
                             extraRecipients=["el-get-devel@tapoueh.org"],
                             mode='problem')]),
    ])

