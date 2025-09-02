import logging
import json
#logging.basicConfig(level=logging.DEBUG)
from wikibaseintegrator import WikibaseIntegrator, datatypes, wbi_exceptions, wbi_helpers, wbi_login
from wikibaseintegrator.wbi_config import config as wbi_config
wb_language = "de"

def login():
    url = 'http://swb.local'
    wbi_config['MEDIAWIKI_API_URL'] = url + '/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = url + ':8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    wbi_config['WIKIBASE_URL'] = 'http://wikibase.svc'

    # user and password of ClientLogin needs to be a valid wiki user (see .env settings)
    login_instance = wbi_login.Clientlogin(user='Admin', password='fadslkju788329ir4hjk')
    wbi_config['USER_AGENT'] = 'MyWikibaseBot/1.0'
    wbi = WikibaseIntegrator(login=login_instance)
    return wbi


def write_properties(wbi, data):
    print('write properties to wikibase...')
    i = 0
    for prop_name in data:
        #check if exist
        propsFound = wbi_helpers.search_entities(
            search_string=prop_name,
            language=wb_language,
            search_type='property',
            login=wbi.login)
        if len(propsFound) > 0:
            prop_id = propsFound[0]
            property = wbi.property.get(prop_id)
        else:  # Create a new item
            property = wbi.property.new()
        property.labels.set(language=wb_language, value=prop_name)
        property.datatype = data[prop_name]
        try:
            property.write()
            i = i + 1
        except:
            print("err")
    print("..." + str(i) + "/"+str(len(data))+" properties written")

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
        if i % 100 == 1 and len(data) >= 100:
            print(str(i) + "/" + str(len(data)))
        if i % 1000 == 1:
            wbi = login()
        #check if item exist:
        itemname = name.lower()
        itemsFound = wbi_helpers.search_entities(
            search_string=itemname,
            language=wb_language,
            search_type='item',
            login=wbi.login)

        if len(itemsFound) > 0:
            itemid = itemsFound[0]
            item = wbi.item.get(itemid)
        else:  # Create a new item
            item = wbi.item.new()

        item.labels.set(language=wb_language, value=itemname)
        if 'description' in data[name]:
            item.descriptions.set(language=wb_language, value=data[name]['description'])
        try:
            item.write()
        except wbi_exceptions.MWApiError as e:
            print('error during write: ' + e.info)
            wbi = login()

    print("..."+str(i)+"/"+str(len(data))+" items written")
    # item.claims.add(data)
    # item.write()


def write_item_claims(wbi, data, ref):
    print('write claims (property values) to wikibase...')
    propID_promotedBy = ref['property'].get('promoviertVon', '')

    i = 0
    toWrite = 0
    written = 0
    total = len(data)
    for item1label in data['item']:
        act_propID = ref['property'].get('item1label')
        i = i + 1
        if i % 100 == 1 and total >= 100:
            print(str(i) + "/" + str(total) + " " + item1label)
        item1id = ref['item'][item1label.lower()]
        item1 = wbi.item.get(entity_id=item1id)
        for property_name in data['item'][item1label]:
            # skip wikibase default properties
            if property_name in ["description"]:
                continue
            toWrite = toWrite + 1
            property_id = ref['property'].get(property_name, '')
            property_type = data['property'][property_name]
            claim = ()
            match property_type:
                case "string":
                    claim = datatypes.String(prop_nr=property_id, value=data['item'][item1label][property_name])
                case "wikibase-item":
                    item2label = str(data['item'][item1label][property_name]).lower()
                    if item2label:
                        item2id = ref['item'][item2label]
                        claim = datatypes.Item(prop_nr=property_id, value=item2id)
                case "time":
                    claim = datatypes.Time(prop_nr=property_id, time=data['item'][item1label][property_name])
                case "globe-coordinate":
                    latLon = data['item'][item1label][property_name].split(',')
                    claim = datatypes.GlobeCoordinate(prop_nr=property_id, latitude=float(latLon[0].strip()),
                                                      longitude=float(latLon[1].strip()))
                case "quantity":
                    claim = datatypes.Quantity(prop_nr=property_id, amount=data['item'][item1label][property_name])
                case "monolingualtext":
                    claim = datatypes.MonolingualText(prop_nr=property_id, text=data['item'][item1label]['text'])
                case _:
                    print("error: item has no valid property type:" + property_type)
            if claim:
                item1.claims.add(claim)
                written = written + 1
            else:
                print("skip empty claim for property: '"+property_name+"' on item: '"+item1label+"'")

        try:
            item1.write()
        except wbi_exceptions.MWApiError as e:
            print('error during write: ' + e.info)
            wbi = login()
    print("..."+str(written)+"/"+str(toWrite)+" claims(property values) written")


def get_references(wbi, data):
    print('get references...')
    result = {'property': {}, 'item': {}}
    print('  >properties...')
    for propname in data['property']:
        prop = wbi_helpers.search_entities(
            search_string=propname,
            language=wb_language,
            search_type='property',
            login=wbi.login)
        result['property'][propname] = prop[0]

    print('  >items...')
    i = 0
    total = len(data['item'])
    for itemkey in data['item']:
        i = i + 1
        if i % 100 == 1 and total >= 100:
            print(str(i) + "/" + str(total))
        itemname = itemkey.lower()
        item = wbi_helpers.search_entities(
            search_string=itemname,
            language=wb_language,
            search_type='item',
            login=wbi.login)
        if item:
            result['item'][itemname] = item[0]
        else:
            print('item not found: ' + itemname)
            print('add missing item...')
            write_items(wbi, {itemname: {itemkey: data['item'][itemkey]}})

    return result


if __name__ == '__main__':
    # read data file
    f = open('data.json')
    data = json.load(f)
    # login to wikibase and write data
    wbi = login()
    write_properties(wbi, data['property'])
    # insert too many items fail often (>2000) use start/end var to insert chunks
    write_items(wbi, data['item'],0,5000)
    ref = get_references(wbi, data)
    print(ref)
    write_item_claims(wbi, data, ref)

    # check if we should create Mediawiki Categories
    #if data["meta"]["create_categories"]:

    # close data file
    f.close()
