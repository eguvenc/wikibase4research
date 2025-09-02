import json
import os
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_exceptions
from wikibaseintegrator import wbi_helpers

######### change wiki language here ###############
wiki_language = 'en'
###################################################

def login(auth=()):
    from wikibaseintegrator import wbi_login, WikibaseIntegrator
    from wikibaseintegrator.wbi_config import config as wbi_config

    ######### change url and credentials here ###############
    url = "http://wb.local/"
    username = os.environ["W4R_MW_ADMIN_USER"]
    pw = os.environ["W4R_MW_ADMIN_PASS"]
    #########################################################

    wbi_config['MEDIAWIKI_API_URL'] = url+'/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = url+':8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    wbi_config['WIKIBASE_URL'] = 'http://wikibase.svc'
    login_instance = wbi_login.Clientlogin(user=username, password=pw)
    wbi_config['USER_AGENT'] = 'MyWikibaseBot/1.0'

    wbi = WikibaseIntegrator(login=login_instance)
    return wbi

def read():
    from wikibaseintegrator import wbi_login, WikibaseIntegrator
    from wikibaseintegrator.wbi_config import config as wbi_config

    url = "http://wb.local"
    wbi_config['MEDIAWIKI_API_URL'] = url+'/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = url+':8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    wbi_config['WIKIBASE_URL'] = 'http://wikibase.svc'

    wbi = WikibaseIntegrator()
    my_first_wikidata_item = wbi.item.get(entity_id='Q3')

    # to check successful installation and retrieval of the data, you can print the json representation of the item
    print(my_first_wikidata_item.get_json())

# dummy method that defines data model and data to import. replace with your own data or load data from file
def get_data():
    return {
        'item':{
            "Person_GordonShumway": {
                'entityType':'person',
                'description': 'Null problemo',
                'name': 'Gordon Shumway',
                "promoviertVon": "Person_AshWilliams"},
            "Person_AshWilliams": {
                'entityType': 'person',
                'name': 'Ash Williams',
                'description': 'Clatu verata nectu',
                "promoviertVon": ""},
            "Aufenthalt_1":{
                'entityType': 'aufenthalt',
                'person': 'Person_GordonShumway',
                'ort': 'Ort_misc',
                'zeit_von': '2023-02-01T00:00:00Z',
                'zeit_bis': '2024-02-15T00:00:00Z'},
            "Aufenthalt_2": {
                'entityType': 'aufenthalt',
                'person': 'Person_GordonShumway',
                'description': '',
                'ort': 'Ort_TIB',
                'zeit_von': '2022-06-01T00:00:00Z',
                'zeit_bis': '2023-01-15T00:00:00Z'},
            'Ort_TIB': {
                'entityType': 'ort',
                'koord': '52.38129832043299,9.720074971993201',
                'name': 'Technische Informationsbibliothek (TIB) Hannover'},
            'Ort_misc': {
                'entityType': 'ort',
                'koord': '52.18129832043299,9.520074971993201',
                'name': 'Somewhere'},
            'Kategorie_root': {
                'entityType': 'Kategorie',
                'name': 'Root Categorie',
                'subCategoryOf': ''},
        },
        'property':{
            'entityType': 'string',
            "promoviertVon": "wikibase-item",
            "name": "string",
            "person": "wikibase-item",
            'ort': 'wikibase-item',
            'zeit_von': 'time',
            'zeit_bis': 'time',
            'koord': 'globe-coordinate',
            'hierarchieLevel': 'quantity',
            'subCategoryOf': 'wikibase-item',
            'text': 'monolingualtext',
            'textItem': 'wikibase-item',
            'paragraphItem': 'wikibase-item',
            'index': 'quantity',
            'annotationType': 'string',
            'annotationSource': 'string',
            'startPos': 'string',
            'endPos': 'string',
            'contributor': 'string',
            'score':'quantity',
            'vocabulary': 'string',
            'linkedItem': 'wikibase-item',
        }
    }

def write_properties(wbi, data):
    print('write properties to wikibase...')
    for prop_name in data:
        #check if exist
        propsFound = wbi_helpers.search_entities(
            search_string=prop_name,
            language=wiki_language,
            search_type='property',
            login=wbi.login)
        if len(propsFound) > 0:
            prop_id = propsFound[0]
            property = wbi.property.get(prop_id)
        else:  # Create a new item
            property = wbi.property.new()
        property.labels.set(language=wiki_language, value=prop_name)
        property.datatype = data[prop_name]
        try:
            property.write()
        except:
            print("err")

def write_items(wbi, data, start=0, end=999999999):
    print('write items to wikibase...')
    import time
    i = 0
    for name in data:
        i = i + 1
        if i < start:
            continue
        if i > end:
            break

        #print(str(i))
        if i % 100 == 1:
            print(str(i)+"/"+str(len(data)))
        if i % 1000 == 1:
            wbi = login()
        #check if item exist:
        itemname = name
        itemsFound = wbi_helpers.search_entities(
            search_string=itemname,
            language=wiki_language,
            search_type='item',
            login=wbi.login)


        if len(itemsFound) > 0:
            itemid = itemsFound[0]
            item = wbi.item.get(itemid)
        else:    # Create a new item
            item = wbi.item.new()

        item.labels.set(language=wiki_language, value=itemname)
        if 'description' in data[name]:
            item.descriptions.set(language=wiki_language, value=data[name]['description'])
        try:
            item.write()
        except wbi_exceptions.MWApiError as e:
            print( 'error during write: '+e.info)
            wbi = login()

def write_item_claims(wbi,items, props,ref):
    print('write claims (property values) to wikibase...')
    i = 0
    toWrite = 0
    written = 0
    total = len(data)
    for item1label in items:
        print(item1label)
        #act_propID = ref['property'].get('item1label')
        i = i + 1
        if i % 100 == 1 and total >= 100:
            print(str(i) + "/" + str(total) + " " + item1label)
        item1id = ref['item'][item1label]
        item1 = wbi.item.get(entity_id=item1id)
        for property_name in items[item1label]:
            # skip wikibase default properties
            if property_name in ["description"]:
                continue
            if property_name in []: # if you want to skip properties from import, add them here
                continue
            if not items[item1label][property_name]:  # if value empty, skip
                continue
            toWrite = toWrite + 1
            property_id = ref['property'].get(property_name, '')
            if property_id == '':
                raise Exception("Unknown property: "+property_name)
            property_type = props[property_name]
            # allow list of values to add multiple statements of same property
            qList = []
            if type(items[item1label][property_name]) is list:
                qList = items[item1label][property_name]
            else:
                qList = [items[item1label][property_name]]

            for value in qList:
                claim = ()
                match property_type:
                    case "string":
                        claim = datatypes.String(prop_nr=property_id, value=str(value).replace("\n", "<br>").strip())
                    case "wikibase-item":
                        item2label = str(value)
                        if item2label:
                            item2id = ref['item'][item2label]
                            claim = datatypes.Item(prop_nr=property_id, value=item2id)
                    case "time":
                        claim = datatypes.Time(prop_nr=property_id, time=value)
                    case "globe-coordinate":
                        latLon = value.split(',')
                        claim = datatypes.GlobeCoordinate(prop_nr=property_id, latitude=float(latLon[0].strip()),
                                                          longitude=float(latLon[1].strip()))
                    case "quantity":
                        if value == "#N/A":
                            continue
                        claim = datatypes.Quantity(prop_nr=property_id, amount=value)
                    case "monolingualtext":
                        claim = datatypes.MonolingualText(prop_nr=property_id, text=value)
                    case _:
                        print("error: item has no valid property type:" + property_type)
                if claim:
                    item1.claims.add(claim)
                    written = written + 1
                else:
                    print("skip empty claim for property: '" + property_name + "' on item: '" + item1label + "'")

        try:
            item1.write()
        except wbi_exceptions.MWApiError as e:
            print('error during write: ' + e.info)
            wbi = login()
    print("..." + str(written) + "/" + str(toWrite) + " claims(property values) written")

def get_references(wbi, data , useRefCache=True):
    refCacheFile = "wb_ref_cache.json"
    if useRefCache and os.path.exists(refCacheFile):
        with open(refCacheFile, 'r', encoding='utf-8') as f:
            print("using ref from cache file!")
            return json.load(f)
    print('get references...')
    result = {'property': {},'item': {}}
    print('  >properties...')
    for propname in data['property']:
        prop = wbi_helpers.search_entities(
            search_string=propname,
            language=wiki_language,
            search_type='property',
            login=wbi.login)
        result['property'][propname] = prop[0]

    print('  >items...')
    i=0
    total = len(data['item'])
    for itemkey in data['item']:
        i = i + 1
        if i % 100 == 1:
            print(str(i)+"/"+str(total))
        itemname = itemkey
        item = wbi_helpers.search_entities(
            search_string=itemname,
            language=wiki_language,
            search_type='item',
            login=wbi.login)
        if item:
            result['item'][itemname] = item[0]
        else:
            print('item not found: '+itemname)
            print('add missing item...')
            write_items(wbi, {itemname: {itemkey: data['item'][itemkey]}})
            result['item'][itemname] = wbi_helpers.search_entities(
            search_string=itemname,
            language=wiki_language,
            search_type='item',
            login=wbi.login)
        f = open(refCacheFile, "w")
        json.dump(result, f)
    return result


if __name__ == '__main__':
    #read() # can be used to test wiki connection
    useRefCache = False # use a cached version of wb data references to save time
    wbi = login()

    # get data to import
    data = get_data()
    # write properties to wikibase
    write_properties(wbi, data['property'])
    # write items to wikibase
    write_items(wbi, data['item'],0,5000)
    # get written wikibase ids (P and Q ids)
    ref = get_references(wbi, data)
    #print(ref)
    # write item statements
    write_item_claims(wbi, data['item'], data['property'],ref)
