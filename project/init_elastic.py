import requests
import json
from project.config import config


def startup_mapping():
    return {
        "Startup": {
            "_all": {"enabled": True},
            "properties": {
                "name": {"type": "string"},
                "website": {"type": "string"},
                "description": {"type": "string"},
                "markets": {"type": "string"}
            }
        }
    }


def generate_search_structure(es):
    # create if not already there
    es.indices.create(index=config['DATABASE_NAME'], ignore=400)

    # tell elastic search what the structure of the user is
    es.indices.put_mapping(index=config['DATABASE_NAME'], doc_type='User', body={
        "User": {
            "_all": {"enabled": True},
            "properties": {
                "email": {"type": "string"},
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "roles": {"type": "string"},
                "interests": {
                    "type": "nested",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"}
                    }
                },
                "skills": {"type": "string"},
                "projects": {
                    "type": "nested",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "details": {
                            "type": "nested",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                            }
                        }
                    }
                }
            }
        }
    })

    es.indices.put_mapping(index=config['DATABASE_NAME'], doc_type='Startup', body=startup_mapping())

    #stupid elasticpy doesn't seem to support suggestions
    payload = {
        "mappings": {
            "skill": {
                "properties": {
                    "name": {"type": "string"},
                    "occurrences": {"type": "integer"},
                    "name_suggest": {
                        "type": "completion"
                    }
                }
            }

        }
    }

    headers = {'content-type': 'application/json'}
    r = requests.put("http://" + config['ELASTIC_HOST'] + ':' + str(config['ELASTIC_PORT']) + "/" +config['DATABASE_NAME']+"-skills",
                     data=json.dumps(payload), headers=headers)


    
    #stupid elasticpy doesn't seem to support suggestions
    payload = {
        "mappings": {
            "market": {
                "properties": {
                    "name": {"type": "string"},
                    "occurrences": {"type": "integer"},
                    "name_suggest": {
                        "type": "completion"
                    }
                }
            }

        }
    }
    headers = {'content-type': 'application/json'}
    r = requests.put("http://" + config['ELASTIC_HOST'] + ':' + str(config['ELASTIC_PORT']) + "/" +config['DATABASE_NAME']+"-markets",
                     data=json.dumps(payload), headers=headers)

