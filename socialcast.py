# Copyright (c) 2013 Niels Henrik Hagen
# (https://github.com/nhhagen & https://bitbucket.org/nhhagen)
# All rights reserved.
# 
# Permission is hereby granted, free  of charge, to any person obtaining
# a  copy  of this  software  and  associated  documentation files  (the
# "Software"), to  deal in  the Software without  restriction, including
# without limitation  the rights to  use, copy, modify,  merge, publish,
# distribute,  sublicense, and/or sell  copies of  the Software,  and to
# permit persons to whom the Software  is furnished to do so, subject to
# the following conditions:
# 
# The  above  copyright  notice  and  this permission  notice  shall  be
# included in all copies or substantial portions of the Software.
# 
# THE  SOFTWARE IS  PROVIDED  "AS  IS", WITHOUT  WARRANTY  OF ANY  KIND,
# EXPRESS OR  IMPLIED, INCLUDING  BUT NOT LIMITED  TO THE  WARRANTIES OF
# MERCHANTABILITY,    FITNESS    FOR    A   PARTICULAR    PURPOSE    AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE,  ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import urllib
from brokers import BaseBroker
from django.utils import simplejson as sj
 
class URLOpener(urllib.FancyURLopener):
    version = 'Bitbucket.org'

    def prompt_user_passwd(self, host, realm):
        return (self.user, self.password)

    """
    Post activity to SocialCast

    Four parameters are expected within the payload['service']:
    url (required) - the URL to the SocialCast community
    group_id (optional) - The id (integer) of a SocialCast group, easiest way to find an id is to use the Groups API 
                        curl -X GET -v --basic -u  "emily@socialcast.com:demo" https://demo.socialcast.com/api/groups.xml
    username (required) - the username to use for authentication against the SocialCast community
    password (required) - the password to use for authentication against the SocialCast community

    Five parameters are expected within the payload['repository']:
    owner (required) - the owner of the repository
    name (required) - the name of the repository
    website (required)
    absolute_url (required)

    Three parameters are expected within the payload['commits']:
    author (required) - if the commit author matches the a SocialCast user (after removing whitespace) a mention on SocialCast happens
    branch (required) - the branch the change was made on
    message (required)
    node (required)
    """ 
class SocialCast(BaseBroker):
    def handle(self, payload):
        api_path = "/api/messages.json"
        url = "%s%s" % (payload['service']['url'], api_path)
        username = payload['service']['username']
        password = payload['service']['password']
        group_id = payload['service']['group_id'] if 'group_id' in payload['service'] else ''
 
        del payload['service']
        del payload['broker']

        repository = payload['repository']
        repo_name = '%s/%s' % (repository['owner'], repository['name'])
        
        s_if_plural = 's' if len(payload['commits']) > 1 else ''
        
        title = '%s commit%s pushed to BitBucket repo %s' % (len(payload['commits']), s_if_plural, repo_name)

        body = ''
        for commit in payload['commits']:
            addedCount = 0
            modifiedCount = 0
            removedCount = 0
            for f in commit['files']:
                if f['type'] == 'added':    addedCount = addedCount + 1
                if f['type'] == 'modified': modifiedCount = modifiedCount + 1
                if f['type'] == 'removed':  removedCount = removedCount + 1

            body += '@%s changed %s +%s ~%s -%s:%s - %s\n' % (commit['author'].replace(' ', ''), commit['branch'], addedCount, modifiedCount, removedCount, commit['node'], commit['message'])
        
        socialCastPayload = urllib.urlencode({"message[title]":title,"message[body]":body, "message[group_id]":group_id})

        opener = self.get_local('opener', URLOpener)
        opener.user = username
        opener.password = password
        opener.open(url, socialCastPayload)

#For test execution
#The username and password provided here are provied by SocialCast to use with their test community
if (__name__ == '__main__'):
    broker = SocialCast()
    payload = {
                'broker': u'socialcast',
                'commits': [{ 
                            'author': u'nhhagen',
                            'branch': u'master',
                    'files': [{'file': u'socialcast.py',
                               'type': u'modified'},
                              {'file': u'.gitignore',
                               'type': u'modified'}],
                    'message': u'added commit messages support, issue #206 fixed',
                    'node': u'ce67db6',
                    'revision': 1650,
                    'size': 684}],
                'repository': { 'absolute_url': u'nhhagen/socialcast-bitbucket-broker',
                'name': u'socialcast-bitbucket-broker',
                'owner': u'nhhagen',
                'slug': u'socialcast-bitbucket-broker',
                'website': u'http://bitbucket.org/'},
                'service': {'password': u'demo', 'username': u'emily@socialcast.com', 'url': u'https://demo.socialcast.com'}
                }

    payload_with_group = {
                'broker': u'socialcast',
                'commits': [{ 
                            'author': u'nhhagen',
                            'branch': u'master',
                    'files': [{'file': u'socialcast.py',
                               'type': u'modified'},
                              {'file': u'.gitignore',
                               'type': u'modified'}],
                    'message': u'added commit messages support, issue #206 fixed',
                    'node': u'ce67db6',
                    'revision': 1650,
                    'size': 684}],
                'repository': { 'absolute_url': u'nhhagen/socialcast-bitbucket-broker',
                'name': u'socialcast-bitbucket-broker',
                'owner': u'nhhagen',
                'slug': u'socialcast-bitbucket-broker',
                'website': u'http://bitbucket.org/'},
                'service': {'password': u'demo', 'username': u'emily@socialcast.com', 'url': u'https://demo.socialcast.com', 'group_id': u'8'}
                }

    broker.handle(payload)
    broker.handle(payload_with_group)
