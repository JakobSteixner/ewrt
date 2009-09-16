#!/usr/bin/env python

""" http.py
    - accesses resources using http """

# (C)opyrights 2008 by Albert Weichselbraun <albert@weichselbraun.net>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib2
from eWRT.config import USER_AGENT, DEFAULT_WEB_REQUEST_SLEEP_TIME
from urlparse import urlsplit
import time
from StringIO import StringIO
from gzip import GzipFile

getHostName = lambda x: "://".join( urlsplit(x)[:2] )

class Retrieve(object):
    """ retrieves URL's using HTTP supporting transparent
        * authentication and
        * compression """

    __slots__ = ('module', 'sleep_time', 'last_access_time')

    def __init__(self, module, sleep_time=DEFAULT_WEB_REQUEST_SLEEP_TIME):
        self.module = module
        self.sleep_time       = sleep_time
        self.last_access_time = 0
        # request object

    def open(self, url, data=None, user=None, pwd=None ):
        """ Opens an URL and returns the matching file object 
            @param[in] url 
            @param[in] data  optional data to submit
            @param[in] user  optional user name
            @param[in] pwd   optional password
            @returns a file object for reading the url
        """
        request = urllib2.Request( url, data )
        request.add_header('User-Agent', USER_AGENT % self.module)
        request.add_header('Accept-encoding', 'gzip')
        self._throttle()

        # handle authentification
        if user and pwd:
            urlObj = urllib2.build_opener( self._getHTTPBasicAuthOpener(url, user, pwd) ).open( request ) 
        else:
            urlObj = urllib2.build_opener().open( request )

        # check whether the data stream is compressed
        if urlObj.headers.get('Content-Encoding') == 'gzip':
            return self._getUncompressedStream( urlObj )

        return urlObj



    @staticmethod
    def _getHTTPBasicAuthOpener(url, user, pwd):
        """ returns an opener, capable of handling http-auth """
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password('realm', getHostName(url), user, pwd)
        return auth_handler

    @staticmethod
    def _getUncompressedStream(urlObj):
        """ transparently uncompressed the given data stream
            @param[in] urlObj 
            @returns an urlObj containing the uncompressed data
        """
        compressedStream = StringIO( urlObj.read() )
        return GzipFile(fileobj=compressedStream) 


    def _throttle( self ):
        """ delays web access according to the content provider's policy """
        if (time.time() - self.last_access_time) < DEFAULT_WEB_REQUEST_SLEEP_TIME:
            time.sleep( self.sleep_time )
        self.last_access_time= time.time()



if __name__ == '__main__':
    
    from unittest import TestCase, main

    class TestHttp(TestCase):
        """ tests the http class """
        TEST_URLS = ('http://www.google.at/search?hl=de&q=andreas&btnG=Google-Suche&meta=', 
                     'http://www.heise.de' )

        def testRetrieval(self):
            """ tries to retrieve the following url's from the list """

            r_handler = Retrieve( self.__class__.__name__ )
            for url in self.TEST_URLS:
                print url
                r=r_handler.open( url )
                r.read()
                r.close()

    main()

