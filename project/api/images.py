from flask import request, Blueprint, request, jsonify, make_response, current_app
from flask.ext.login import login_user, login_required, logout_user, abort
from project import utils
from project.services.auth import Auth
from flask.ext.api import FlaskAPI, exceptions
from flask.ext.api.status import *
from bson.objectid import ObjectId
from wand.image import Image
from werkzeug import secure_filename
from models.user import getUserID
from models.image import create_image, find_image_by_id

ALLOWED_EXTENSIONS = set(['bmp', 'png', 'jpg', 'jpeg', 'gif'])

PROFILE_SIZE = 280 #280 x 280px
PROFILE_FORMAT = 'jpeg'
PROFILE_QUALITY = 85

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

blueprint = Blueprint(
    'images', __name__
)

def crop_image(image):
    crop = image.clone()
    square_size = min(crop.height, crop.width)
    crop.transform('%ix%i'%(square_size, square_size),
        '%ix%i'%(PROFILE_SIZE, PROFILE_SIZE))
    crop.format = PROFILE_FORMAT
    crop.compression_quality = PROFILE_QUALITY
    return crop

# Fix POST hang by giving preflight the OPTIONS OK it needs. Hacky but works.
@blueprint.route('/images',  methods=['OPTIONS'])
def handle_preflight():
    return current_app.make_default_options_response()

@blueprint.route('/images', methods=['POST'])
@Auth.require(Auth.USER)
def upload_image():
    request_error = ''
    user_id = getUserID('me')
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        try:
            image_blob = crop_image(Image(file=file)).make_blob()
            image_id = create_image(image_blob, user_id)
            return jsonify(error=None, imageID=str(image_id) + '.' + PROFILE_FORMAT)
        except Exception as e:
            request_error = str(e)
    return jsonify(error=request_error), HTTP_400_BAD_REQUEST

@blueprint.route('/images/<imageid>.'+PROFILE_FORMAT, methods=['GET'])
@Auth.require(Auth.USER)
def get_image(imageid):
    entry = find_image_by_id(imageid)
    if entry is None:
        return '', HTTP_404_NOT_FOUND

    response = make_response(entry['data'])
    response.headers['Content-Type'] = 'image/jpeg'
    return response

@blueprint.route('/images/<imageid>.'+PROFILE_FORMAT, methods=['DELETE'])
@Auth.require(Auth.USER)
def delete_image(imageid):
    entry = find_image_by_id(imageid)
    if entry is None:
        return '', HTTP_404_NOT_FOUND

    if str(entry['owner']) != str(getUserID('me')): # TODO: Add admin override
        return '', HTTP_401_UNAUTHORIZED

    entry.delete()
    return '', HTTP_200_OK