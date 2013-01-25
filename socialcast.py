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

    Five parameters are expected within the payload['service']:
    url (required) - the URL to the SocialCast community
    group_id (optional) - The id (integer) of a SocialCast group, easiest way to find an id is to use the Groups API 
                        curl -X GET -v --basic -u  "emily@socialcast.com:demo" https://demo.socialcast.com/api/groups.xml
    username (required) - the username to use for authentication against the SocialCast community
    password (required) - the password to use for authentication against the SocialCast community
    branch_filter (optional) - if set only changes to that branch will be pushed to the SocialCast community

    Thow parameters are expected within the payload['repository']:
    owner (required) - the owner of the repository
    name (required) - the name of the repository

    Four parameters are expected within the payload['commits']:
    author (required) - if the commit author matches the a SocialCast user (after removing whitespace) a mention on SocialCast happens
    branch (required) - the branch the change was made on
    message (required)
    node (required)

    One paramter is expected within the commit[files]
    type (required) - expected values are "added", "modified", "removed", the type of change done to a file
    """ 
class SocialCast(BaseBroker):
    def handle(self, payload):
        api_path = "/api/messages.json"
        url = "%s%s" % (payload['service']['url'], api_path)
        username = payload['service']['username']
        password = payload['service']['password']
        group_id = payload['service']['group_id'] if 'group_id' in payload['service'] else ''
        branch_filter = payload['service']['branch_filter'] if 'branch_filter' in payload['service'] else None
 
        del payload['service']
        del payload['broker']

        repository = payload['repository']
        repo_name = '%s/%s' % (repository['owner'], repository['name'])
        
        body = ''
        valid_commits = 0
        for commit in payload['commits']:
            if commit['branch'] == branch_filter or branch_filter == None: #Only build commit messages for valid branches
                valid_commits = valid_commits + 1
                addedCount = 0
                modifiedCount = 0
                removedCount = 0
                for f in commit['files']:
                    if f['type'] == 'added':    addedCount = addedCount + 1
                    if f['type'] == 'modified': modifiedCount = modifiedCount + 1
                    if f['type'] == 'removed':  removedCount = removedCount + 1

                body += '%s made changes to %s ' % (commit['author'], commit['branch'])

                files = list()
                if addedCount > 0: 
                    files.append('added %s' % addedCount)
                if modifiedCount > 0:
                    files.append('modified %s' % modifiedCount)
                if removedCount > 0:
                    files.aappenddd('removed %s' % removedCount)

                s_if_plural = 's' if sum([addedCount, modifiedCount, removedCount]) > 1 else ''
                body += '%s file%s' % (', '.join(files), s_if_plural)

                body += ' in changeset %s, message was \"%s\"\n' % (commit['node'], commit['message'])

        if valid_commits > 0: #Only push to SocialCast if there are valid commits
            s_if_plural = 's' if valid_commits > 1 else ''
            title = '%s commit%s pushed to BitBucket repo %s' % (valid_commits, s_if_plural, repo_name)

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
                               'type': u'modified'}],
                    'message': u'added commit messages support, issue #206 fixed',
                    'node': u'ce67db6',
                    'revision': 1650,
                    'size': 684},
                    { 
                            'author': u'nhhagen',
                            'branch': u'master',
                    'files': [{'file': u'socialcast.py',
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

    payload_with_branch_filter = {
                'broker': u'socialcast',
                'commits': [{ 
                            'author': u'nhhagen',
                            'branch': u'featureX',
                    'files': [{'file': u'socialcast.py',
                               'type': u'modified'}],
                    'message': u'added commit messages support, issue #206 fixed',
                    'node': u'ce67db6',
                    'revision': 1650,
                    'size': 684},
                    { 
                            'author': u'nhhagen',
                            'branch': u'master',
                    'files': [{'file': u'socialcast.py',
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
                'service': {'password': u'demo', 'username': u'emily@socialcast.com', 'url': u'https://demo.socialcast.com', 'branch_filter': u'master'}
            }

    payload_with_branch_filter_matching_branch = {
                'broker': u'socialcast',
                'commits': [{ 
                            'author': u'nhhagen',
                            'branch': u'featureX',
                    'files': [{'file': u'socialcast.py',
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
                'service': {'password': u'demo', 'username': u'emily@socialcast.com', 'url': u'https://demo.socialcast.com', 'branch_filter': u'featureX'}
            }

    payload_with_group = {
                'broker': u'socialcast',
                'commits': [{ 
                            'author': u'nhhagen',
                            'branch': u'master',
                    'files': [{'file': u'socialcast.py',
                               'type': u'modified'},
                              {'file': u'.gitignore',
                               'type': u'added'}],
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
    broker.handle(payload_with_branch_filter)
    broker.handle(payload_with_branch_filter_matching_branch)
