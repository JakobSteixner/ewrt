#!/usr/bin/env python

""" @package eWRT.ws.flickr
    retrieve flickr related tags and tag counts.    
"""

# (C)opyrights 2008-2010 by Albert Weichselbraun <albert@weichselbraun.net>
#                           Heinz-Peter Lang <heinz@langatium.net>
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


__version__ = "$Header$"

import sys
import re
from eWRT.access.http import Retrieve
from eWRT.ws.TagInfoService import TagInfoService
from urlparse import urlsplit

class Flickr(TagInfoService):
    """ retrieves data using the del.icio.us API """

    FLICKR_TAG_URL = "http://www.flickr.com/photos/tags/%s" 
    RE_TAG_COUNT = re.compile('<div class="Results">\(([\d,]+) upload')
    RE_TAG_CONTAINER = re.compile('<p>Related tags:<br>(.*?)</p>', re.IGNORECASE|re.DOTALL)
    RE_RELATED_TAGS = re.compile('<a.*?">(.*?)</a>', re.IGNORECASE | re.DOTALL)

    __slots__ = ()

    @staticmethod
    def getTagInfo( tags ):
        """ 
            @param   tags   A list of tags to retrieve information for
            @returns        the number of bookmarks using the given tags
        """
        assert isinstance(tags, list) or isinstance(tags, tuple)

        url = Flickr.FLICKR_TAG_URL % "+".join(tags)        
        content = Flickr.get_content(url)
        return Flickr._parse_tag_counts(content)


    @staticmethod
    def getRelatedTags( tags ):
        """ fetches the related tags with their overall count
            @param  tags    list of tags
            @returns        list of related tags 
        """
        assert isinstance(tags, list) or isinstance(tags, tuple)

        url = Flickr.FLICKR_TAG_URL % "+".join(tags)
        content = Flickr.get_content(url)
        tag_container = Flickr.RE_TAG_CONTAINER.findall( content )
        related_tags_with_count = []

        if len(tag_container) > 0:

            related_tags = re.sub('</?b>', '', tag_container[0])
            related_tags = Flickr.RE_RELATED_TAGS.findall(related_tags)

            for tag in related_tags:
                related_tags_with_count.append((tag, Flickr.getTagInfo( (tag,) )))

        return related_tags_with_count


    # 
    # helper functions
    #
    @staticmethod
    def _parse_tag_counts( content ):
        """ parses flickrs html content and returns the number of counts for the tags """
        m=Flickr.RE_TAG_COUNT.search( content )
        return int(m.group(1).replace(",","")) if m else 0


    @staticmethod
    def get_content( url ):
        """ returns the content from Flickr """
        assert( url.startswith("http") )

        f = Retrieve(Flickr.__name__).open(url)
        content = f.read()
        f.close()
        return content

class TestFlickr( object ):
    
    def testMultipleTags( self ):
        """ verifies whether multiple tags return results different from single tags """
        assert Flickr.getRelatedTags( ("berlin", "dom")) != Flickr.getRelatedTags( ("berlin",) ) 
        assert Flickr.getTagInfo( ("berlin", "dom") ) != Flickr.getTagInfo( ("berlin",) ) 

    def testTagInfo( self ):
        """ test the tag info """
        for tags in ( ('berlin','dom') , ('vienna',),  ('castle',) ):
            assert Flickr.getTagInfo( tags ) > 0

    def testRelatedTags( self ):
        """ test related tags by retrieving related tags for the following tags """
        for tags in ( ('berlin', 'dom'),  ):
            relatedTags = Flickr.getRelatedTags( tags )
            print tags, relatedTags
            assert len( relatedTags  ) > 0


if __name__ == '__main__':
    print Flickr.getTagInfo( ("berlin", "dom") ), "counts"
    print Flickr.getRelatedTags( ("berlin", "dom", ) ), "counts"
    
