#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------
# Program Name:           fujian
# Program Description:    An HTTP server that executes Python code.
#
# Filename:               fujian/__main__.py
# Purpose:                This starts everything.
#
# Copyright (C) 2015, 2016, 2017 Christopher Antila
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#--------------------------------------------------------------------------------------------------
'''
Main Fujian module.
'''

from collections import defaultdict
import shutil
import sys
import tempfile
import traceback

from lychee.workflow.session import InteractiveSession
from tornado import ioloop, web, websocket

import fujian


_ACCESS_CONTROL_ALLOW_ORIGIN = 'http://localhost:8000'

EXEC_GLOBALS = {'__name__': '__main__', '__builtins__': __builtins__}
SESSION = 'Placeholder for an InteractiveSession'
TEMPDIRS = 'Placeholder for the tempdirs defaultdict'


# set the type that a string should be, according to Python 2 or 3
if 'unicode' in dir():
    StringType = unicode
else:
    StringType = str


def make_tempdir():
    '''
    Create a new temporary directory for *Fujian*.
    '''
    return tempfile.mkdtemp()


class StdoutHandler(object):
    '''
    This is a replacement for :func:`sys.stdout` and :func:`sys.stderr` that collects its output
    for retrieval with :meth:`get`.

    This class supports the required :meth:`write` method for an output stream, but no output is
    emitted under any circumstances except as returned from the :meth:`get` method.
    '''

    def __init__(self):
        "Create a new :class:`StdoutHandler`."
        self.stuff = ''

    def write(self, write_this):
        '''
        Append ``write_this`` to this :class:`StdoutHandler` instance's data buffer.

        :param str write_this: Data to append.
        '''
        self.stuff += write_this

    def get(self):
        '''
        Retrieve all data submitted to this :class:`StdoutHandler` with :meth:`write`.

        :returns: The buffered data.
        :rtype: str
        '''
        return self.stuff


def make_new_stdout():
    '''
    Make a new stdout and stderr, with the request's EXEC_GLOBALS, for a single request.
    '''
    exec_this = 'import sys\nsys.stdout = StdoutHandler()\nsys.stderr = StdoutHandler()\ndel sys'
    exec(exec_this, EXEC_GLOBALS, {'StdoutHandler': StdoutHandler})  # pylint: disable=exec-used


def get_from_stdout():
    '''
    Get what was written to stdout, with the request's EXEC_GLOBALS, in this request.
    '''
    local_locals = {}
    exec_this = 'import sys\npost = sys.stdout.get()\ndel sys'
    exec(exec_this, EXEC_GLOBALS, local_locals)  # pylint: disable=exec-used
    return local_locals['post']


def get_from_stderr():
    '''
    Get what was written to stderr, with the request's EXEC_GLOBALS, in this request.
    '''
    local_locals = {}
    exec_this = 'import sys\npost = sys.stderr.get()\ndel sys'
    exec(exec_this, EXEC_GLOBALS, local_locals)  # pylint: disable=exec-used
    return local_locals['post']


def myprint(this):
    '''
    Prints "this" using the original stdout, even when it's been replaced. For use in debugging
    ``fujian`` itself.
    '''
    sys.__stdout__.write('{}\n'.format(this))


def get_traceback():
    '''
    Get a traceback of the most recent exception raised in the subinterpreter.
    '''
    typ, val, trace = sys.exc_info()
    # err_name = getattr(typ, '__name__', StringType(typ))
    # err_msg = StringType(val)
    err_trace = ''.join(traceback.format_exception(typ, val, trace))
    return err_trace


def execute_some_python(code):
    '''
    Execute some Python code in the "EXEC_GLOBALS" namespace.

    :param str code: The Python code to execute.
    :returns: A dictionary with "stdout", "stderr", "return", and possibly "traceback" keys.
    :rtype: dict

    The dictionary returned contains the values written to stdout and stderr during the code
    execution. If a value is written to the global :data:`fujian_return` variable, that is returned
    as the value of the "return" key. If the code raises an unhandled exception, the traceback
    appears is the value of the "traceback" key.

    .. note:: All values in the dictionary are guaranteed to be the Unicode string type appropriate
        to the Python version in use.
    '''
    # clear stdout, stderr, and fujian_return
    print(code)
    make_new_stdout()
    EXEC_GLOBALS['fujian_return'] = ''
    EXEC_GLOBALS['session'] = SESSION
    EXEC_GLOBALS['show'] = fujian.bridge.get_show_abjad(SESSION)

    post = {}

    try:
        exec(code, EXEC_GLOBALS)  # pylint: disable=exec-used
    except Exception:  # pylint: disable=broad-except
        post['traceback'] = StringType(get_traceback())

    post['stdout'] = StringType(get_from_stdout())
    post['stderr'] = StringType(get_from_stderr())
    post['return'] = StringType(EXEC_GLOBALS['fujian_return'])
    del EXEC_GLOBALS['fujian_return']

    return post


class FujianHandler(web.RequestHandler):
    '''
    Connect with clients via HTTP.
    '''

    def set_default_headers(self):
        '''
        Set the "Server" and "Access-Control-Allow-Origin" response headers.
        '''
        self.set_header('Server', 'Fujian/{}'.format(fujian.__version__))
        self.set_header('Access-Control-Allow-Origin', _ACCESS_CONTROL_ALLOW_ORIGIN)

    def get(self):
        '''
        Reply with an empty response body. Basically this is a ping request.
        '''
        self.write('')

    def post(self):
        '''
        Execute Python code submitted in the request body, and return results of the computation.

        .. note:: The global :data:`fujian_return` variable is set to a zero-length string before
            any code is executed, so it is guaranteed not to contain data from a previous request.

        **Response Body**

        If the response code is 200, it's a JSON object with three members: ``stdout``, ``stderr``,
        and ``return``. If the response code is 400 (meaning there was an unhandled exception) the
        object also contains a ``traceback`` member.

        All of these are strings. The ``stdout`` and ``stderr`` members are the contents of the
        corresponding stdio streams. The ``return`` member is the value stored in the global
        ``fujian_return`` variable at the end of the call. If present, ``traceback`` contains the
        traceback of the most recent unhandled exception.
        '''

        code = self.request.body
        if not isinstance(code, StringType):
            code = StringType(code)

        post = execute_some_python(code)
        if 'traceback' in post:
            self.set_status(400)

        self.write(post)


class FujianWebSocketHandler(websocket.WebSocketHandler):
    '''
    Connect with clients via WebSocket.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Set the local flag to know the connection is closed. Also set global :const:`FUJIAN_WS`.
        '''
        self._is_open = False
        EXEC_GLOBALS['FUJIAN_WS'] = self
        websocket.WebSocketHandler.__init__(self, *args, **kwargs)

    def is_open(self):
        '''
        Determine whether the WebSocket connection is currently open.

        If there is no WebSocket currently open, any calls to
        :meth:`~tornado.websocket.WebSocketHandler.write_message` will raise a
        :exc:`tornado.websocket.WebSocketClosedError`.
        '''
        return self._is_open

    def open(self, **kwargs):
        '''
        Set the flag that avoids delaying small messages to save bandwidth. Since Fujian is intended
        only for use on ``localhost``, any delay would be detrimental to the user experience, and
        morever there is no reason to save bandwidth.

        Also set the local flag to know the connection is open.
        '''
        self.set_nodelay(True)
        self._is_open = True
        EXEC_GLOBALS['FUJIAN_WS'] = self
        execute_some_python('import lychee.signals\nlychee.signals.set_fujian(FUJIAN_WS)')
        websocket.WebSocketHandler.open(self, **kwargs)

    def on_close(self):
        '''
        Set the local flag to know the connection is closed.
        '''
        self._is_open = False
        EXEC_GLOBALS['FUJIAN_WS'] = None
        # should we do something with self.close_code and self.close_reason?
        websocket.WebSocketHandler.on_close(self)

    def check_origin(self, origin):
        '''
        If supplied, Tornado uses this method to allow checking the Origin request header, to verify
        that the request is indeed coming from somewhere we are okay with. For us that means
        localhost, with or without HTTPS.
        '''
        permitted_origins = ('http://localhost:', 'https://localhost:', 'file://')
        for permitted_origin in permitted_origins:
            if origin.startswith(permitted_origin):
                return True

        return False

    def on_message(self, message):
        '''
        Execute Python code submitted in a WebSocket message.

        This works much like :meth:`~fujian.__main__.FujianHandler.post` except this method will not
        necessarily produce a response to the client. If the code writes to ``stdout`` or ``stderr``,
        or sets the global ``fujian_return`` variable, a JSON response will be sent to the client
        in the same way as :meth:`~fujian.__main__.FujianHandler.post`. If the code execution raises
        an unhandled exception, a ``traceback`` member will be included, in the same way as
        :meth:`~fujian.__main__.FujianHandler.post`.

        If the code does not raise an unhandled exception, write to ``stdout`` or ``stderr``, or
        set the global ``fujian_return`` variable, no message will be sent to the client about the
        success or failure of code execution.

        Furthermore, and quite unlike a connection to :class:`~fujian.__main__.FujianHandler`,
        messages may be sent to the client without first being requested. This is caused by any
        code that calls :meth:`~tornado.websocket.WebSocketHandler.write_message` on the global
        :const:`FUJIAN_WS` object installed by :class:`~fujian.__main__.FujianWebSocketHandler`.
        '''

        if not isinstance(message, StringType):
            message = StringType(message)

        if message[0] == '{':
            # TODO: this doesn't (yet) catch all exceptions
            fujian.bridge.process_signal(self, message, SESSION, TEMPDIRS)
        else:
            post = execute_some_python(message)
            if 'traceback' in post:
                self.write_message(post)
            elif len(post['stdout']) > 0 or len(post['stderr']) > 0 or len(post['return']) > 0:
                self.write_message(post)



# key is whatever; value is pathname to a directory created by mkdtemp()
TEMPDIRS = defaultdict(make_tempdir)
try:
    # so that Abjad outputs to a Fujian-managed directory
    abjad_tempdir = TEMPDIRS['abjad']
    abjad_script = (
        'from abjad import *\n'
        "abjad_configuration['abjad_output_directory'] = '{0}'\n".format(abjad_tempdir)
        )
    execute_some_python(abjad_script)

    SESSION = InteractiveSession(vcs=None)

    APP = web.Application([
        (r'/', FujianHandler),
        (r'/websocket/', FujianWebSocketHandler),
    ])
    APP.listen(1987)
    ioloop.IOLoop.current().start()
finally:
    for each_dir in TEMPDIRS.itervalues():
        shutil.rmtree(each_dir)
