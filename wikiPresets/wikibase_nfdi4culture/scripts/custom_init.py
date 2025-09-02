from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.datatypes import extra
from wikibaseintegrator.wbi_exceptions import MissingEntityException
import pandas
import pathlib
import rdflib
import requests
import time
import tqdm
import os
import csv
import dotenv
import sys
import argparse
 
parser = argparse.ArgumentParser(description='Initialize Wikibase with custom settings')
parser.add_argument('--skip-formatters', action='store_true', help='Skip processing formatter IDs')
args = parser.parse_args()
 
instance_id='P1'
subclass_id='P60'
subproperty_id='P66'
 
 
def pull_attribute(row, pre, filt):
 
    ''' Pull specific attribute from graph. '''
 
    iri = row['iri']
    for s,p,o in data_model.triples((rdflib.URIRef(iri), pre, None)):
        if filt in str(o):
            return str(o)
 
def pull_attribute_ml(row, pre, filt):
 
    ''' Pull specific attribute from graph - multilingual. '''
 
    iri = row['iri']
    labels = {}
    for s,p,o in data_model.triples((rdflib.URIRef(iri), pre, None)):
        labels[o.language] = str(o)
    return labels
 
try:
    data_model = rdflib.Graph().parse(pathlib.Path.cwd() / 'model.ttl')
except FileNotFoundError:
    r = requests.get('https://gitlab.com/nfdi4culture/ta1-data-enrichment/wikibase-model/-/raw/main/wikibase_generic_model.ttl')
    data_model = rdflib.Graph().parse(data=r.content, format='ttl')
 
# compile entities
 
entities = list()
for x in [rdflib.OWL.Class, rdflib.OWL.ObjectProperty, rdflib.OWL.DatatypeProperty, rdflib.OWL.NamedIndividual]:
    entities += [{'iri':s, 'type':str(o)} for s,p,o in data_model.triples((None, rdflib.RDF.type, x))]
dataframe = pandas.DataFrame(entities)
 
# build a table of entities to write.
 
dataframe.loc[dataframe.type.str.contains('Class|Individual', na=False), 'wikibase_type'] = 'item'
dataframe.loc[dataframe.type.str.contains('Property', na=False), 'wikibase_type'] = 'property'
 
dataframe['wikibase_id'] = dataframe.apply(pull_attribute, pre=rdflib.SKOS.note, filt='Wikibase ID', axis=1)
dataframe['wikibase_datatype'] = dataframe.apply(pull_attribute, pre=rdflib.SKOS.note, filt='datatype', axis=1)
dataframe['label'] = dataframe.apply(pull_attribute_ml, pre=rdflib.RDFS.label, filt='', axis=1)
dataframe['description'] = dataframe.apply(pull_attribute_ml, pre=rdflib.URIRef('http://purl.org/dc/elements/1.1/description'), filt='', axis=1)
dataframe['alias'] = dataframe.apply(pull_attribute, pre=rdflib.SKOS.altLabel, filt='', axis=1)
 
# id wrangling.
 
dataframe['wikibase_datatype'] = dataframe['wikibase_datatype'].str.replace('Wikibase datatype:','').str.strip()
dataframe['wikibase_id'] = dataframe['wikibase_id'].str.replace('Wikibase ID:','').str.strip()
dataframe['wikibase_id'] = dataframe['wikibase_id'].str.replace('Q','').str.strip()
dataframe['wikibase_id'] = dataframe['wikibase_id'].str.replace('P','')
dataframe['wikibase_id'] = dataframe['wikibase_id'].str.strip().astype('int')
dataframe = dataframe.sort_values(by='wikibase_id')
 
# pull subclass and subprop statements.
 
subclass_dataframe = pandas.DataFrame(columns=['iri', 'subclass_of'])
for s,p,o in data_model.triples((None, rdflib.RDFS.subClassOf, None)):
    subclass_dataframe.loc[len(subclass_dataframe)] = [s, o]
dataframe = pandas.merge(dataframe, subclass_dataframe, on='iri', how='left')
 
subprop_dataframe = pandas.DataFrame(columns=['iri', 'subproperty_of'])
for s,p,o in data_model.triples((None, rdflib.RDFS.subPropertyOf, None)):
    subprop_dataframe.loc[len(subprop_dataframe)] = [s, o]
dataframe = pandas.merge(dataframe, subprop_dataframe, on='iri', how='left')
 
#pull instance of
instance_dataframe = pandas.DataFrame(columns=['iri', 'instance_of'])
for s,p,o in data_model.triples((None, rdflib.RDF.type, None)):
    instance_dataframe.loc[len(instance_dataframe)] = [s, o]
filtered_instance_dataframe = instance_dataframe[~instance_dataframe['instance_of'].str.contains('http://www.w3.org/2002/07/owl', na=False)]
dataframe = pandas.merge(dataframe, filtered_instance_dataframe, on='iri', how='left')
 
# writing config ( all from dotenv)
domain = "http://wikibase/"
# if no trailing slash, add it.
if domain[-1] != '/':
    domain += '/'
wbi_config['MEDIAWIKI_API_URL'] = domain+'api.php'
wbi_config['USER_AGENT'] = 'generic data model'
login_instance = wbi_login.Login(user=os.environ.get('W4R_MW_ADMIN_USER'), password=os.environ.get('W4R_MW_ADMIN_PASS'))
wbi = WikibaseIntegrator(login=login_instance)
 
 
 
# write entities.
 
for x in tqdm.tqdm(dataframe.to_dict('records')):
    if x['wikibase_type'] == 'property':
        ident = f"P{x['wikibase_id']}"
        r = requests.get(f'{domain}wiki/Special:EntityData/{ident}.ttl', verify=False)
        print(f"Requesting property data, status is {r.status_code}")
 
        entity = None
        if r.status_code == 404:
            try:
                entity = wbi.property.new(datatype=x['wikibase_datatype'])
                entity.write()
                print(f"Creating property {ident}")
                time.sleep(2)  # Wait 2 seconds
            except ValueError as e:
                print(f"Error creating property {ident}: {str(e)}")
                sys.exit(1)
 
        print(f"Writing property {ident}")
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                updater = wbi.property.get(ident)
                for key, value in x['label'].items():
                    updater.labels.set(key, value)
                for key, value in x['description'].items():
                    if len(value) > 250:
                        value = value[:240] + " ..."
                    updater.descriptions.set(key, value)
                updater.aliases.set('en', x['alias'])
                updater.write()
                break  # Success, exit the retry loop
            except MissingEntityException as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)  # Wait before retrying
                else:
                    print(f"Failed to update property {ident} after {max_retries} attempts")
                    raise
 
    elif x['wikibase_type'] == 'item':
        ident = f"Q{x['wikibase_id']}"
        r = requests.get(f'{domain}wiki/Special:EntityData/{ident}.ttl', verify=False)
        print(f"Requesting item data, status is {r.status_code}")
 
        entity = None
        if r.status_code == 404:
            try:
                entity = wbi.item.new()
                entity.write()
                print(f"Creating item {ident}")
                time.sleep(2)  # Wait 2 seconds
            except ValueError as e:
                print(f"Error creating item {ident}: {str(e)}")
                sys.exit(1)
 
        print(f"Writing item {ident}")
        max_retries = 3
        retry_count = 0
        while retry_count < max_retries:
            try:
                updater = wbi.item.get(ident)
                for key, value in x['label'].items():
                    updater.labels.set(key, value)
                for key, value in x['description'].items():
                    if len(value) > 250:
                        value = value[:240] + " ..."
                    updater.descriptions.set(key, value)
                updater.aliases.set('en', x['alias'])
                updater.write()
                break  # Success, exit the retry loop
            except MissingEntityException as e:
                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(5)  # Wait before retrying
                else:
                    print(f"Failed to update item {ident} after {max_retries} attempts")
                    raise
 
 
# reserve items up to 200.
 
for x in tqdm.tqdm(range(200)):
 
    ident = f"Q{x}"
    r = requests.get(f'{domain}wiki/Special:EntityData/{ident}.ttl', verify=False)
    if r.status_code == 404:
        entity = wbi.item.new()
        entity.write()
 
# write subclass and subproperty claims.
 
for x in tqdm.tqdm(dataframe.to_dict('records')):
    try:
        if type(x['subproperty_of']) != float:
            target = dataframe.loc[dataframe.iri.isin([x['subproperty_of']])].iloc[0]['wikibase_id']
            prop = wbi.property.get('P'+str(x['wikibase_id']))
            claim = datatypes.Property(prop_nr=subproperty_id, value='P'+str(target))
            prop.claims.add(claim)
            prop.write()
 
        if type(x['subclass_of']) != float:
            target = dataframe.loc[dataframe.iri.isin([x['subclass_of']])].iloc[0]['wikibase_id']
            item = wbi.item.get('Q'+str(x['wikibase_id']))
            claim = datatypes.Item(prop_nr=subclass_id, value='Q'+str(target))
            item.claims.add(claim)
            item.write()
    except Exception:
        print(x)
        print("Subproperty or Subclass could not be set for " + x['wikibase_type'] + str(x["wikibase_id"]))
#write instance of claims
 
for x in tqdm.tqdm(dataframe.to_dict('records')):
    try:
        if type(x['instance_of']) != float:
            target = dataframe.loc[dataframe.iri.isin([x['instance_of']])].iloc[0]['wikibase_id']
            item = wbi.item.get('Q'+str(x['wikibase_id']))
            claim = datatypes.Item(prop_nr=instance_id, value='Q'+str(target))
            item.claims.add(claim)
            item.write()
    except Exception:
        print("setting Instance of claim failed for " + x['wikibase_type'] + str(x["wikibase_id"]))
 
if not args.skip_formatters:
    try:
        file_path = 'formatterids.txt'
        def ensure_property_exists(property_id, label, description, datatype):
            """Make sure a property exists before trying to use it"""
            try:
                # Try to get property
                wbi.property.get(property_id)
                print(f"Property {property_id} already exists")
            except MissingEntityException:
                # Create property if it doesn't exist
                print(f"Creating property {property_id}")
                new_prop = wbi.property.new(datatype=datatype)
                new_prop.labels.set('en', label)
                new_prop.descriptions.set('en', description)
                new_prop.write()
 
        # Ensure formatter URL and URI properties exist before using them
        ensure_property_exists('P68', 'formatter URI', 'URI pattern for external identifier', 'string')
        ensure_property_exists('P69', 'formatter URL', 'URL pattern for external identifier', 'string')
        print(f"Processing formatter IDs from {file_path}")
 
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
 
            for row in reader:
                qid = row.get('qid')
                name = row.get('name')
                print(f"Processing: {name} ({qid})")
 
                try:
                    # Try to get existing property
                    item = wbi.property.get(qid)
                    print(f"Found existing property for {name}")
                except MissingEntityException:
                    # If property doesn't exist, create new one
                    print(f"Creating new property for {name}")
                    new_property = wbi.property.new(datatype='string')  # Specify appropriate datatype
                    new_property.labels.set(language='en', value=name)
                    new_property.descriptions.set(language='en', value=f"Formatter ID for {name}")
                    new_property.write()
                    item = new_property
 
                # Add claims
                print(f"Adding/updating claims for {name}")
                claim_uri = datatypes.String(prop_nr='P68', value=row.get('uri'))
                item.claims.add(claim_uri)
                claim_url = datatypes.String(prop_nr='P69', value=row.get('url'))
                item.claims.add(claim_url)
                item.write()
                print(f"Completed processing {name}")
 
        print("Formatter ID processing completed")
    except FileNotFoundError:
        print(f"Error: formatterids.txt file not found - skipping formatter ID processing")
    except Exception as e:
        print(f"Error processing formatter IDs: {str(e)}")
else:
    print("Skipping formatter ID processing")
 