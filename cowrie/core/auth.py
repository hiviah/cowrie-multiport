# Copyright (c) 2009-2014 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

import string
import json
from os import path
from sys import modules
from random import randint

from zope.interface import implements

from twisted.python import log

# by Walter de Jong <walter@sara.nl>
class UserDB(object):

    def __init__(self, cfg):
        self.userdb = []
        self.userdb_file = '%s/userdb.txt' % cfg.get('honeypot', 'data_path')
        self.load()

    def load(self):
        """
        load the user db
        """

        f = open(self.userdb_file, 'r')
        while True:
            line = f.readline()
            if not line:
                break

            line = string.strip(line)
            if not line:
                continue

            if line.startswith('#'):
                continue

            (login, uid_str, passwd) = line.split(':', 2)

            uid = 0
            try:
                uid = int(uid_str)
            except ValueError:
                uid = 1001

            self.userdb.append((login, uid, passwd))

        f.close()

    def save(self):
        """
        save the user db
        """

        # Note: this is subject to races between cowrie instances, but hey ...
        f = open(self.userdb_file, 'w')
        for (login, uid, passwd) in self.userdb:
            f.write('%s:%d:%s\n' % (login, uid, passwd))
        f.close()

    @staticmethod
    def demangle_password(password):
        """Demangle password from jsonified in-band signaling from mitmproxy, e.g.
        {"pass": "zaq12wsx", "remote": "82.165.199.122", "turris_id": "00000005000002ee"}

        @returns tuple (password, remote, turris_id). Last two fields are None
                if it's not valid json.
        """
        try:
            d = json.loads(password)
            return (d.get("pass", ""), d.get("remote"), d.get("turris_id"))
        except ValueError:
            return (password, None, None)
        except AttributeError:
            return (password, None, None)

    def checklogin(self, thelogin, thepasswd, src_ip='0.0.0.0'):
        """
        check entered username/password against database
        note that it allows multiple passwords for a single username
        it also knows wildcard '*' for any password
        prepend password with ! to explicitly deny it. Denials must come before wildcards

        Hack: this will try to de-mangle password from json format that is sent
        by mitmproxy.
        """
        thepasswd = self.demangle_password(thepasswd)[0]

        for (login, uid, passwd) in self.userdb:
            # explicitly fail on !password
            if login == thelogin and passwd == '!' + thepasswd:
                return False
            if login == thelogin and passwd in (thepasswd, '*'):
                return True
        return False

    def user_exists(self, thelogin):
        for (login, uid, passwd) in self.userdb:
            if login == thelogin:
                return True
        return False

    def user_password_exists(self, thelogin, thepasswd):
        for (login, uid, passwd) in self.userdb:
            if login == thelogin and passwd == thepasswd:
                return True
        return False

    def getUID(self, loginname):
        for (login, uid, passwd) in self.userdb:
            if loginname == login:
                return uid
        return 1001

    def allocUID(self):
        """
        allocate the next UID
        """

        min_uid = 0
        for (login, uid, passwd) in self.userdb:
            if uid > min_uid:
                min_uid = uid
        return min_uid + 1

    def adduser(self, login, uid, passwd):
        if self.user_password_exists(login, passwd):
            return
        self.userdb.append((login, uid, passwd))
        self.save()

class AuthRandom(object):
    """
    Alternative class that defines the checklogin() method.
    Users will be authenticated after a random number of attempts.
    """

    def __init__(self, cfg):
        # Default values
        self.mintry, self.maxtry, self.maxcache = 2, 5, 10

        # Are there auth_class parameters?
        if cfg.has_option('honeypot', 'auth_class_parameters'):
            parameters = cfg.get('honeypot', 'auth_class_parameters')
            parlist = parameters.split(',')
            if len(parlist) == 3:
                self.mintry = int(parlist[0])
                self.maxtry = int(parlist[1])
                self.maxcache = int(parlist[2])

        if self.maxtry < self.mintry:
            self.maxtry = self.mintry + 1
            log.msg('maxtry < mintry, adjusting maxtry to: %d' % self.maxtry)
        self.uservar = {}
        self.uservar_file = '%s/uservar.json' % cfg.get('honeypot', 'data_path')
        self.loadvars()

    def loadvars(self):
        # Load user vars from json file
        if path.isfile(self.uservar_file):
            with open(self.uservar_file, 'rb') as fp:
                try:
                    self.uservar = json.load(fp)
                except:
                    self.uservar = {}

    def savevars(self):
        # Save the user vars to json file
        data = self.uservar
        # Note: this is subject to races between cowrie logins
        with open(self.uservar_file, 'wb') as fp:
            json.dump(data, fp)

    def checklogin(self, thelogin, thepasswd, src_ip):
        """
        Every new source IP will have to try a random number of times between
        'mintry' and 'maxtry' before succeeding to login.
        All username/password combinations  must be different.
        The successful login combination is stored with the IP address.
        Successful username/passwords pairs are also cached for 'maxcache' times.
        This is to allow access for returns from different IP addresses.
        Variables are saved in 'uservar.json' in the data directory.
        """

        auth = False
        userpass = thelogin + ':' + thepasswd

        if not 'cache' in self.uservar:
            self.uservar['cache'] = []
        cache = self.uservar['cache']

        # Check if it is the first visit from src_ip
        if src_ip not in self.uservar:
            self.uservar[src_ip] = {}
            ipinfo = self.uservar[src_ip]
            ipinfo['try'] = 0
            if userpass in cache:
                log.msg('first time for %s, found cached: %s' % (src_ip, userpass))
                ipinfo['max'] = 1
                ipinfo['user'] = thelogin
                ipinfo['pw'] = thepasswd
                auth = True
                self.savevars()
                return auth
            else:
                ipinfo['max'] = randint(self.mintry, self.maxtry)
                log.msg('first time for %s, need: %d' % (src_ip, ipinfo['max']))

        ipinfo = self.uservar[src_ip]

        # Fill in missing variables
        if not 'max' in ipinfo:
            ipinfo['max'] = randint(self.mintry, self.maxtry)
        if not 'try' in ipinfo:
            ipinfo['try'] = 0
        if not 'tried' in ipinfo:
            ipinfo['tried'] = []

        # Don't count repeated username/password combinations
        if userpass in ipinfo['tried']:
            log.msg('already tried this combination')
            self.savevars()
            return auth

        ipinfo['try'] += 1
        attempts = ipinfo['try']
        need = ipinfo['max']
        log.msg('login attempt: %d' % attempts)

        # Check if enough login attempts are tried
        if attempts < need:
            self.uservar[src_ip]['tried'].append(userpass)
        elif attempts == need:
            ipinfo['user'] = thelogin
            ipinfo['pw'] = thepasswd
            cache.append(userpass)
            if len(cache) > self.maxcache:
                cache.pop(0)
            auth = True
        # Returning after successful login
        elif attempts > need:
            if not 'user' in ipinfo or not 'pw' in ipinfo:
                log.msg('return, but username or password not set!!!')
                ipinfo['tried'].append(userpass)
                ipinfo['try'] = 1
            else:
                log.msg('login return, expect: [%s/%s]' % (ipinfo['user'], ipinfo['pw']))
                if thelogin == ipinfo['user'] and thepasswd == ipinfo['pw']:
                    auth = True
        self.savevars()
        return auth

# vim: set sw=4 et:
