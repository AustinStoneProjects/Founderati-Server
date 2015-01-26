from bson.objectid import ObjectId
from project import Follows
from mongokit import Document
from project import connection
from models.user import getUserID, findUserByID
from models.startup import find_startup_by_id


@connection.register
class Follow(Document):
    __collection__ = 'Follows'
    __database__ = 'thehookemup'
    structure = {
        'followees': [{'_id': ObjectId, 'type': basestring}],
        'followers': [{'_id': ObjectId, 'type': basestring}],
        'entityType': basestring
    }

    required_fields = ['entityType']

coll = Follows


def find_follows_by_id(entity_id):
    entity_id = getUserID(entity_id) if entity_id == 'me' else entity_id
    return coll.Follow.find_one({'_id': ObjectId(entity_id)})


def inject_entities(action):
    def inject(*args, **kwargs):
        entities = [find_follows_by_id(entity_id) for entity_id in args]
        return action(*entities)
    return inject


def inject_entity(action):
    def inject(*args, **kwargs):
        entity_id = kwargs['entity_id']
        if not entity_id:
            raise Exception('An entity id must be provided')
        return action(find_follows_by_id(entity_id))
    return inject


def get_or_create(entity_id, entity_type):
    entity_id = getUserID(entity_id) if entity_id == 'me' else entity_id
    entity_follows = coll.Follow.find_one({'_id': entity_id})
    if not entity_follows:
        find = find_startup_by_id if entity_type == 'startup' else findUserByID
        if find(entity_id):
            entity_follows = coll.Follow()
            entity_follows['_id'] = entity_id
            entity_follows['entityType'] = entity_type
        else:
            raise Exception('%s does not exist' % entity_type)
    return entity_follows


def add_or_pass(followers_follows, entity):
    if not filter(lambda e: e['_id'] == entity['_id'], followers_follows):
        followers_follows.append(entity)


def follow_entity(entity_id, entity_type):
    entity_id = ObjectId(entity_id)
    user_id = ObjectId(getUserID('me'))

    if entity_id == user_id:
        raise Exception('Cannot follow self')

    entity_follows = get_or_create(entity_id, entity_type)
    user_follows = get_or_create(user_id, 'user')

    add_or_pass(entity_follows['followers'], {'_id': user_id, 'type': 'user'})
    add_or_pass(user_follows['followees'], {'_id': entity_id, 'type': entity_type})

    entity_follows.save()
    user_follows.save()
    return user_follows['followees']


@inject_entity
def count(entity):
    followee_count = len(entity['followees']) if entity else 0
    follower_count = len(entity['followers']) if entity else 0
    return {'followees': followee_count, 'followers': follower_count}


@inject_entity
def followers(entity):
    return entity['followers'] if entity else None


@inject_entity
def followees(entity):
    return entity['followees'] if entity else None


@inject_entities
def unfollow(follower, followee):
    def find_remove(entity, to_remove, role):
        entity[role] = filter(lambda f: f['_id'] != to_remove['_id'], entity[role])
        entity.save()

    find_remove(followee, follower, 'followers')
    find_remove(follower, followee, 'followees')

    return follower


def user_unfollow(entity_id):
    return unfollow('me', entity_id)














