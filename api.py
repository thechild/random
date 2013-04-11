# from https://bitbucket.org/bivab/pocket-v3/src/6c4ff63e5aab/pocketv3/api.py?at=default

import requests
import json
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler


class authenticated(object):
    instance = None

    def __init__(self, f):
        self.f = f

    def __call__(self, **kwargs):
        assert self.instance is not None
        auth_info = self.check_auth()
        kwargs.update(auth_info)
        return self.f(self.instance, **kwargs)

    def __get__(self, instance,
        instancetype):
        self.instance = instance
        return self

    def check_auth(self):
        assert self.instance is not None
        if(hasattr(self.instance, 'authentication') and
                self.instance.authentication is None):
            self.instance.authenticate()
        return {'access_token': self.instance.access_token,
                'consumer_key': self.instance.consumer_key}


class API(object):
    headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Accept': 'application/json',
    }

    def __init__(self, consumer_key):
        self.consumer_key = consumer_key
        self.actions = []
        self.authentication = None

    @property
    def access_token(self):
        return self.authentication.access_token

    @property
    def request_token(self):
        return self.authentication.code

    def authenticate(self, access_token=None):
        self.authentication = Authenticator(self.consumer_key)
        if access_token is None:
            self.authentication.auth()
        else:
            self.authentication.access_token = access_token

    #@authenticated
    # Note: If you are only adding a single item, the /v3/add endpoint should
    # be used.
    #def add(self, **kwargs):
    #    url = 'https://getpocket.com/v3/add'
    #    self._validate_keys('add', kwargs)
    #    return json.loads(requests.post(url, data=json.dumps(kwargs),
    #                                         headers=self.headers).content)

    @authenticated
    def get(self, **kwargs):
        # force a commit to write all changes before reading
        self.commit()
        url = 'https://getpocket.com/v3/get'
        self._validate_keys('get', kwargs)
        return json.loads(requests.post(url,
            data=json.dumps(kwargs),
            headers=self.headers).content)

    _valid_keys = {
        'get': ['state', 'favorite', 'tag', 'contentType', 'sort',
            'detailType', 'search', 'domain', 'since', 'count', 'offset',
            'consumer_key', 'access_token'],
        'add': ['url', 'title', 'tags', 'tweet_id'],
        'modify': ['actions', 'consumer_key', 'access_token'],
        'tag_rename': ['item_id', 'old_tag', 'new_tag'],
    }
    for a in ['archive', 'favorite', 'unfavorite', 'delete', 'tags_clear']:
        _valid_keys[a] = ['item_id']
    for a in ['tags_add', 'tags_remove', 'tags_replace']:
        _valid_keys[a] = ['item_id', 'tags']
    for a in _valid_keys:
        _valid_keys[a].append('time')

    def _validate_keys(self, action, kwargs):
        # TODO: Better errors
        assert len(set(
            kwargs.keys()).difference(
                self._valid_keys[action])) == 0

    @authenticated
    def commit(self, **kwargs):
        if len(self.actions) == 0:
            print 'nothing to commit'
            return
        #
        actions = []
        for action, args in self.actions:
            args['action'] = action
            actions.append(args)
        self.actions = []
        #
        url = 'https://getpocket.com/v3/send'
        kwargs['actions'] = actions
        self._validate_keys('modify', kwargs)
        return json.loads(requests.post(url, data=json.dumps(kwargs),
                                             headers=self.headers).content)


class transaction(object):
    def __init__(self, api, *args, **kwargs):
        self.api = api

    def __enter__(self, *args, **kwargs):
        pass

    def __exit__(self, *args, **kwargs):
        self.api.commit()


def action_builder(action):
    def f(self, **kwargs):
        self._validate_keys(action, kwargs)
        self.actions.append((action, kwargs))
    f.__name__ = action
    return f
for action in ['add', 'archive', 'favorite', 'unfavorite', 'delete',
                'tags_add', 'tags_remove', 'tags_replace', 'tags_clear',
                'tag_rename']:
    setattr(API, action, action_builder(action))


def wait_for_response(port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Authentication worked!\n")
            self.wfile.write(str(self.headers))
            print str(self.headers)
    server = HTTPServer(("localhost", port), Handler)
    server.handle_request()


class Authenticator(object):

    URLs = {'request_token':   'https://getpocket.com/v3/oauth/request',
            'authorize_token': 'https://getpocket.com/auth/authorize?'
                               'request_token=%(request_token)s'
                               '&redirect_uri=%(redirect_uri)s',
            'access_token':    'https://getpocket.com/v3/oauth/authorize'
    }
    headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-Accept': 'application/json',
    }

    def __init__(self, consumer_key):
        self.consumer_key = consumer_key

    def auth(self):
        self.code = self.get_request_token()
        self.authorize_with_pocket()
        self.access_token, self.username = self.get_access_token()
        return self.access_token

    # XXX make sure to catch all exceptions either from pocket or from local
    # connectivity issues
    def get_request_token(self):
        """Step 2: Obtain a request token"""
        params = {
                'consumer_key': self.consumer_key,
                'redirect_uri': 'is-this-even-used',
                'state': 'foo'
        }
        resp = requests.post(self.URLs['request_token'],
                             data=json.dumps(params),
                             headers=self.headers)
        if resp.status_code != 200:
            assert 0, 'expect 200 response'
        return json.loads(resp.content)['code']

    def authorize_with_pocket(self):
        """
        Step 3: Redirect user to Pocket to continue authorization
        Step 4: Receive the callback from Pocket
        """
        import webbrowser
        webbrowser.open(
                self.URLs['authorize_token'] % {
                'request_token': self.code,
                'redirect_uri': 'http://localhost:8000'
        })
        wait_for_response(8000)

    def get_access_token(self):
        """
        Step 5: Convert a request token into a Pocket access token
        """

        params = {
                'consumer_key': self.consumer_key,
                'code': self.code,
        }
        resp = requests.post(self.URLs['access_token'],
                             data=json.dumps(params),
                             headers=self.headers)

        if resp.status_code != 200:
            assert 0
        res = json.loads(resp.content)
        return res['access_token'], res['username']


if __name__ == '__main__':
    import os
    import pickle
    import sys
    f = os.path.expanduser(os.path.join('~', '.config', 'pocket.txt'))
    if os.path.exists(f):
        with file(f, 'r') as target:
            data = pickle.load(target)
        consumerkey = data['consumer_key']
        api = API(consumerkey)
        api.authenticate(data['access_token'])
    else:
        assert len(sys.argv) > 1, 'pass consumerkey on the commandline when ' \
                                  'calling this file for the first time'
        consumerkey = sys.argv[1]
        api = API(consumerkey)
        api.authenticate()
        data = {'consumer_key': consumerkey,
                'access_token': api.access_token}
        with file(f, 'w') as target:
            pickle.dump(data, target)