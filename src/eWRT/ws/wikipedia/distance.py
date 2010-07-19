#!/usr/bin/env python
"""
   @package eWRT.ws.wikipedia.distance
   wikipedia "click" distance between concepts
"""

# -----------------------------------------------------------------------------------
# (C)opyrights 2010 by Albert Weichselbraun <albert@weichselbraun.net>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# -----------------------------------------------------------------------------------

__author__   = "albert"
__revision__ = "$Revision: 1 $"

from eWRT.util.cache import DiskCached
from eWRT.access.db import PostgresqlDb
from eWRT.config import DATABASE_CONNECTION

class WikiDistance(object):
    
    escape_terms = staticmethod( lambda tt:", ".join( ["'%s'" % t.replace("'", "''") for t in tt]) ) 
    
    def __init__(self):
        """ open the database connection """
        self.db = PostgresqlDb( **DATABASE_CONNECTION['wikipedia'])

    def isSibling(self, t1, t2):
        """ determines whether the given concepts are siblings
            @param[in] t1   first term
            @param[in] t2   second term
            @return True if both terms are siblings
        """
        tt = WikiDistance.escape_terms( (t1,t2) ) 
        q="SELECT * FROM vw_siblings WHERE dname IN (%s) AND sname IN (%s)" % (tt, tt)
        return len(self.db.query(q)) > 0 

    def isSameAs(self, t1, t2):
        """ determines whether the given terms refer to the same concept
            @param[in] t1   first term
            @param[in] t2   second term
            @return True if both terms refer to the same concept
        """
        tt = WikiDistance.escape_terms( (t1,t2) )
        q="SELECT * FROM vw_sameas WHERE dname IN (%s) AND sname IN (%s)" % (tt, tt)
        return len(self.db.query(q)) > 0 
        
        

class TestWikiDistance(object):
    
    def __init__(self):
        self.wd = WikiDistance()
        
    def testSameAs(self):
        """ tests the sameAs method """
        assert self.wd.isSameAs("cpu", "central processing unit")
        assert not self.wd.isSameAs("cpu", "desk")
        
    def testIsSibling(self):
        """ tests whether terms are siblings """
        assert self.wd.isSibling("swimming (sport)", "front crawl")
        assert self.wd.isSibling("swimming (sport)", "butterfly stroke")
        assert not self.wd.isSibling("cpu", "front crawl")

    def testTermPairs(self):
        """ test specific term pairs"""
        assert self.wd.isSibling("design area", "risk") == False

if __name__ == '__main__':
    pass
    