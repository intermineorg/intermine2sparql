# es2virtuoso.py

# DB.DBA.RDF_DEFAULT_USER_PERMS_SET ('nobody', 7);

'''
RDF_OBJ_FT_RULE_ADD (null, null, 'All');
VT_INC_INDEX_DB_DBA_RDF_OBJ ();

urilbl_ac_init_db();
s_rank();
'''

import rdflib

from elasticsearch import Elasticsearch, helpers

import json
import requests
from datetime import datetime

es_in = Elasticsearch("http://es.kibio.science:80")
print(es_in)

from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://192.168.3.189:8890/sparql")
print(sparql)

_context_cache = {}

def context_cache(context_url):

    try:
        _context_cache[context_url]
    except (KeyError):
        print('get context from URL:', context_url)
        context = requests.get(context_url).text
        _context_cache[context_url] = json.loads(context)
  
    return(_context_cache[context_url])


# context_cache('http://es.kibio.science/bio2rdf/_source/mirbase')

def es2rdf(es_in, indexName, skip, end):

    results = helpers.scan(es_in, index=indexName, query ={'query':{'match_all':{}}}, size = 100, scroll = "5m", clear_scroll=True)

    ctr = 0
    strLen = 0
    triples = 0
    skip = 170000
    skip = 500000
    end = 1000000

    print(datetime.now(), ctr, 'documents', triples, 'triples', strLen, 'bytes')
    
    for jsonDoc in results:
        ctr = ctr + 1
        
        if ctr % (end/100) == 0:
            print(datetime.now(), ctr, 'documents', triples, 'triples', strLen, 'bytes')

        if ctr < skip:
            continue
        elif ctr > end:
            break
        else:
            jsonDoc = jsonDoc['_source']
            
            jsonDoc['@context'] = context_cache(jsonDoc['@context'])
            strLen = strLen + len(jsonDoc)
            #graphRdf.parse(data=json.dumps(jsonDoc), format='json-ld')
            
            g = rdflib.Graph().parse(data=jsonDoc, format='json-ld')
            #print(ctr, error, doc_uri, len(g))
            #g.serialize(format="nt", destination="temp.nt")
            doc_nt = g.serialize(format="nt")
            #print(len(doc_nt.split('\n')))
            triples = triples + len(doc_nt.split('\n'))
            
            #try:
            sparql.setQuery("INSERT INTO graph <http://intermine.bio2rdf.org> {" + doc_nt + "}")
            result = sparql.query().convert()
            #print(result)
            #except:
            #    print('Virtuoso ERROR')

    print(datetime.now(), ctr, 'documents', triples, 'triples', strLen, 'bytes')
    
es2rdf(es_in, 'intermine_jsonld', 0, 100000)
