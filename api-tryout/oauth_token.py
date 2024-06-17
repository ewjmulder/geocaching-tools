#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Script to get a valid oauth token response from the Geocaching.com website
# Will use saved cookies or ask for credentials
# Username can be provided by setting the GC_USERNAME env var
# Adapted from https://github.com/btittelbach/gctools - geocachingsitelib.py

from __future__ import print_function
import sys
import os
import requests
from http.cookiejar import LWPCookieJar
import re
import types
from io import StringIO
import urllib.parse as urlparse
from lxml import etree

#### Global Constants ####

gc_auth_uri_ = "https://www.geocaching.com/account/login?ReturnUrl=%2Fplay%2Fsearch"

default_config_dir_ = os.path.join(os.path.expanduser('~'),".local","share","gctools")
auth_cookie_default_filename_ = "gctools_cookies"

gc_debug = False

#### Exceptions ####

class HTTPError(Exception):
    pass

class GeocachingSiteError(Exception):
    pass

class NotLoggedInError(Exception):
    pass


#### Internal Helper Functions ####

def _debug_print(context,*args):
    if gc_debug:
        print(u"\n\n=============== %s ===============" % context,file=sys.stderr)
        print(*args,file=sys.stderr)

def _did_request_succeed(r):
    if "error" in r.__dict__:
        return r.error is None
    elif "status_code" in r.__dict__:
        return r.status_code in [requests.codes.ok, 302]
    else:
        assert False

def _init_parser():
    global parser_, xml_parser_
    parser_ = etree.HTMLParser(encoding = "utf-8")
    xml_parser_ = etree.XMLParser(encoding="utf-8")

parser_ = None
_init_parser()

def _ask_usr_pwd():
    if allow_use_wx:
        try:
            import wx
            dlg = wx.TextEntryDialog(parent=None,message="Please enter your geocaching.com username")
            if dlg.ShowModal() != wx.ID_OK:
                raise NotLoggedInError("User aborted username/password dialog")
            usr = dlg.GetValue()
            dlg.Destroy()
            dlg = wx.PasswordEntryDialog(parent=None,message="Please enter your geocaching.com password")
            if dlg.ShowModal() != wx.ID_OK:
                raise NotLoggedInError("User aborted username/password dialog")
            pwd = dlg.GetValue()
            dlg.Destroy()
            return (usr,pwd)
        except Exception as e:
            print(e)
            if gc_debug:
                raise e
    import getpass
    print("Please provide your geocaching.com login credentials:")
    usr = os.environ.get("GC_USERNAME")
    if usr:
        print("Got username " + usr + " from env var GC_USERNAME")
    else:
        print("Env var GC_USERNAME not set, please enter username manually")
        usr = input("Username: ")
    pwd = getpass.getpass()
    return (usr,pwd)

def _request_for_hidden_inputs(uri):
    gcsession = getDefaultInteractiveGCSession()
    r = gcsession.req_get(uri)
    if _did_request_succeed(r):
        return _parse_for_hidden_inputs(uri, r.content)
    else:
        return ({}, uri)

def _parse_for_hidden_inputs(uri, content):
    post_data = {}
    formaction = uri
    tree = etree.fromstring(content, parser_)
    formelem = tree.find(".//form")
    if not formelem is None:
        for input_elem in formelem.findall(".//input[@type='hidden']"):
            post_data[input_elem.get("name")] = input_elem.get("value")
        formaction=urlparse.urljoin(uri,formelem.get("action"))
    return (post_data, formaction)

def _config_file(filename):
    if not os.path.isdir(default_config_dir_):
        os.makedirs(default_config_dir_)
    filepath = os.path.join(default_config_dir_, os.path.basename(filename))
    return filepath

def _delete_config_file(filename):
    filepath = os.path.join(default_config_dir_, os.path.basename(filename))
    try:
        os.unlink(filepath)
    except:
        pass

def _seek0_files_in_dict(d):
    if isinstance(d,dict):
        for i in d.values():
            if isinstance(i,file):
                i.seek(0)
            elif isinstance(i,tuple) and isinstance(i[1],file):
                i[1].seek(0)
    return d

def _splitList(lst,n):
    i=0
    while i < len(lst):
        yield lst[i:i+n]
        i+=n

#### Login / Requests-Lib Decorator ####

class GCSession(object):
    def __init__(self, gc_username, gc_password, cookie_session_filename, ask_pass_handler):
        self.logged_in = 0 #0: no, 1: yes but session may have time out, 2: yes
        self.ask_pass_handler = ask_pass_handler
        self.gc_username = gc_username
        self.gc_password = gc_password
        self.cookie_session_filename = cookie_session_filename
        self.user_agent_ = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:54.0) Gecko/20100101 Firefox/54.0"
        self.session = requests.Session()
        if self._haveCookieFilename():
            self.session.cookies = LWPCookieJar(_config_file(self.cookie_session_filename))

    def _save_cookie_login(self):
        _debug_print("save cookies", self.session.cookies)
        self.session.cookies.save(ignore_discard=True)

    def _load_cookie_login(self):
        self.session.cookies.load(ignore_discard=True)
        _debug_print("loaded cookies", self.session.cookies)

    def _haveUserPass(self):
        return isinstance(self.gc_username, str) and isinstance(self.gc_password, str)

    def _haveCookieFilename(self):
        return isinstance(self.cookie_session_filename, str)

    def _askUserPass(self):
        if isinstance(self.ask_pass_handler, types.FunctionType):
            try:
                (self.gc_username, self.gc_password) = self.ask_pass_handler()
            except Exception as e:
                _debug_print("_askUserPass",e)
                return False
        return self._haveUserPass()

    def login(self):
        if not self._haveUserPass():
            raise Exception("Login called without known username/passwort")
        remember_me = self._haveCookieFilename()

        headers = {
            "User-Agent":self.user_agent_
            }

        # Get a cookie and the anti-forgery token
        r = self.session.get(gc_auth_uri_, allow_redirects = True, headers = headers)
        post_data , formaction = _parse_for_hidden_inputs(gc_auth_uri_, r.content)

        post_data.update({
            "UsernameOrEmail":self.gc_username,
            "Password":self.gc_password,
        })

        headers.update({"Referer" : gc_auth_uri_ })

        # Log in
        r = self.session.post(formaction, data = post_data, allow_redirects = True, headers = headers)

        # Check for cookie
        login_ok = _did_request_succeed(r) and "gspkauth" in [cookie.name for cookie in self.session.cookies]

        if not login_ok:
            return False
        if remember_me:
            self._save_cookie_login()
        return login_ok

    def invalidate_cookie(self):
        self.session.cookies.clear()
        if self._haveCookieFilename():
            _delete_config_file(self.cookie_session_filename)

    def loadSessionCookie(self):
        if not self._haveCookieFilename():
            return False
        try:
            self._load_cookie_login()
            return "gspkauth" in [cookie.name for cookie in self.session.cookies]
        except:
            self.invalidate_cookie()
            return False

    def _check_login(self):
        if self.logged_in > 0:
            return True
        if self.loadSessionCookie():
            self.logged_in = 1
            return True
        if not self._haveUserPass():
            if not self._askUserPass():
                raise NotLoggedInError("Don't know login credentials and can't ask user interactively")
        if not self.login():
            raise NotLoggedInError("login failed, wrong username/password")
        self.logged_in = 2
        return True

    def _check_is_session_valid(self, content):
        if content.find(b"id=\"ctl00_ContentBody_cvLoginFailed\"") >= 0 \
        or content.find(b'<a id="hlSignIn" accesskey="s" title="Sign In" class="SignInLink" href="/login/">Sign In') >= 0 \
        or content.find(b'<h2>Object moved to <a href="https://www.geocaching.com/login/?RESET=Y&amp;redir=') >= 0:
            self.invalidate_cookie()
            self.logged_in = 0
            return False
        return True

    def req_wrap(self, reqfun):
        attempts = 2
        while attempts > 0:
            self._check_login()
            attempts -= 1
            r = reqfun()
            _debug_print("req_wrap","uri: %s\n" % r.url,"attempts: %d\n" % attempts, r.content)
            if _did_request_succeed(r):
                if self._check_is_session_valid(r.content):
                    return r
            else:
                raise HTTPError("Recieved HTTP Error "+str(r.status_code))
        raise NotLoggedInError("Request to geocaching.com failed")

    def req_get(self, uri):
        return self.req_wrap(lambda : self.session.get(uri, headers = {"User-Agent":self.user_agent_, "Referer":uri}))

    def req_post(self, uri, post_data, files = None):
        return self.req_wrap(lambda : self.session.post(uri, data = post_data, files = _seek0_files_in_dict(files), allow_redirects = False, headers = {"User-Agent":self.user_agent_, "Referer":uri}))

    def req_post_json(self, uri, json_data):
        return self.req_wrap(lambda : self.session.post(uri, json = json_data, allow_redirects = False, headers = {"User-Agent":self.user_agent_, "Referer":uri}))

_gc_session_ = False
#gc_username = "Team_Spoorloos"
#gc_password = "joja37"
gc_username = None
gc_password = None
be_interactive = True
allow_use_wx = False

def getDefaultInteractiveGCSession():
    global _gc_session_
    if not isinstance(_gc_session_, GCSession):
        _gc_session_ = GCSession( gc_username = gc_username, gc_password = gc_password, cookie_session_filename = auth_cookie_default_filename_, ask_pass_handler = _ask_usr_pwd if be_interactive else None)
    return _gc_session_

def urlopen(url):
    gcsession = getDefaultInteractiveGCSession()
    r = gcsession.req_get(url)
    return StringIO(r.text)

# Default action: print the oauth token, either using saved cookie or re-logging in if needed.
print(urlopen("https://www.geocaching.com/account/oauth/token").getvalue())
