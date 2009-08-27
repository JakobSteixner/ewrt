# fetches for an ContentID or GazEntry-ID where it is located
# e.g. for Vienna: Europe/Austria/Vienna

import sys
from eWRT.access.db import PostgresqlDb

class Gazetteer(object):
    QUERY_HAS_PARENT = '''
        SELECT parent_id 
        FROM gazetteerentity JOIN locatedin ON (gazetteerentity.id = locatedin.child_id)
        WHERE child_id = %d'''

    QUERY_DATA= '''
        SELECT * FROM gazetteerentry_ordered_names WHERE entity_id = %d '''
       
    QUERY_CONTENT_ID = '''
        SELECT gazetteer_id FROM content_id_gazeteer_id WHERE content_id = %d '''

    parents = []

    ## init - establishes the db-connections
    def __init__(self):
        """ implement me """
        self.db = PostgresqlDb("gazetteer", "xmhawk.ai.wu.ac.at", "", "")
        self.db.connect()
        self.db2 = PostgresqlDb("geoEval", "xmdimrill.ai.wu.ac.at", "", "")
        self.db2.connect()

    ## returns the location of the content ID
    # @param content_id
    # @return list of locaions, e.g. ['Europa', 'France', 'Centre']
    def getGeoNameFromContentID(self, content_id):

        id = content_id
        query = self.QUERY_CONTENT_ID % content_id 
        result = self.db2.query(query)

        if result == []:
            return 'ContentID not found!'
        else:
            gaz_id = result[0]['gazetteer_id']
            return self.getGeoNameFromGazetteerID(gaz_id)

    ## returns the location of the GazetteerEntry ID  
    # @param gazetteer-entry ID  
    # @return list of locaions, e.g. ['Europa', 'France', 'Centre']
    def getGeoNameFromGazetteerID(self, gazetteer_id):
        
        self.parents = []

        result = self.__getGazetteer(gazetteer_id)
        result.reverse()

        if result == []:
            return 'GazetteerID not found!'
        else:
            return result

    def getGeoNameFromString(self, name):
        """ implement me """
        query = '''
            SELECT entity_id, ispreferredname, lang, gazetteerentry_id
            FROM gazetteerentry_ordered_names
            WHERE name LIKE '%s' '''

        list = []

        for result in self.db.query(query % name):
            tmp = self.getGeoNameFromGazetteerID(result['entity_id'])
            list.append(tmp)
        
        return list


    ## builds the full location
    # @param id
    # @returns list of locations
    def __getGazetteer(self, id):
        list = []
        list.append(self.__getData(id))

        parent = self.__hasParent(id)

        if parent:
            list.extend(self.__getGazetteer(parent))

        return list

    ## gets the preferred name for the location
    # @param id
    # @returns preferred name
    def __getData(self, id):
        """ """ 
        query = self.QUERY_DATA % id
        result = self.db.query(query)

        for data in result:

            if data['ispreferredname']:
                return data['name']

            elif data['lang'] == 'en':
                return data['name']
                
            elif data['lang'] == '':
                return data['name']

    ## checks if the given ID has a parent
    # @param ID of the child
    # @return false or ID of the parent 
    def __hasParent(self, child_id):
        query = self.QUERY_HAS_PARENT % child_id
        result = self.db.query(query)
        # todo: funktioniert nicht mit 1++ parents  

        #for result in self.db.query(query):
        #parent_id = result[0]['parent_id']
        """
        if self.parent.index(parent_id):
            return 0        
        else 
            return parent_id
        """
        if result == []:
            return 0 
        else:
            return result[0]["parent_id"]

if __name__ == "__main__":

    a = Gazetteer()
    if sys.argv.__len__() > 1:
        print a.getGeoNameFromContentID(sys.argv[1])
    else:
        print a.getGeoNameFromContentID(86597672)
        print a.getGeoNameFromGazetteerID(95078)
        print a.getGeoNameFromGazetteerID(959484848078)
        print a.getGeoNameFromString('Vienna')
