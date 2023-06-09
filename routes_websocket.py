import json
import time

import ml_config

from image import file_upload as _file_upload
from image import image as _image
from permission import permission_user
import user_auth
import websocket_clients as _websocket_clients

from blog import blog as _blog
from lend_library import lend_library as _lend_library
from user import user as _user

config = ml_config.get_config()

def routeIt(route, data, auth):
    msgId = data['_msgId'] if '_msgId' in data else ''
    ret = { 'valid': '0', 'msg': '', '_msgId': msgId }

    # Check permissions.
    perms = [
        # Save is more dangerous than get; for performance / speed, allow most get calls, unless
        # it returns sensitive information.
        # All allowed get
        # Sensitive, or performance intenstive get
        # [none yet]
        # Save
        "logout",
        "saveImage",
    ]

    userIdRequired = [
        "removeLendLibraryItem",
        "saveLendLibraryItem",
        "saveUser",
    ]

    admin = [
        "removeBlog",
        "saveBlog",
    ]
    if route in perms or route in userIdRequired or route in admin:
        if len(auth['user_id']) == 0:
            ret['msg'] = "Empty user id."
            return ret

    if route in perms or route in admin:
        allowed = 0
        if "_" in auth['user_id']:
            ret['msg'] = "Invalid user id"
            return ret

        if permission_user.LoggedIn(auth['user_id'], auth['session_id']):
            allowed = 1

        if not allowed:
            ret['msg'] = "Permission denied"
            return ret

    if route in admin:
        if permission_user.IsAdmin(auth['user_id']):
            allowed = 1
        else:
            ret['msg'] = "Admin privileges required"
            return ret

    # We must support at least 2 versions since frontend (mobile apps) will
    # not instant update in sync with breaking changes on backend. BUT to keep
    # code clean, force update for earlier versions.
    allowedVersions = ['0.0.0', '0.0.1']

    # if route == 'route1':
    #     ret = route1(data)
    # elif route == 'route2':
    #     ret = { 'hello': 'route 2' }

    if route == 'getAllowedVersions':
        ret = { 'valid': '1', 'msg': '', 'versions': allowedVersions }
    elif route == 'ping':
        ret = { 'valid': '1', 'msg': '' }

    elif route == 'signup':
        roles = data['roles'] if 'roles' in data else ['student']
        ret = user_auth.signup(data['email'], data['password'], data['first_name'], data['last_name'],
            roles)
        if ret['valid'] and 'user' in ret and ret['user']:
            # Join (to string) any nested fields for C# typings..
            if 'roles' in ret['user']:
                # del ret['user']['roles']
                ret['user']['roles'] = ",".join(ret['user']['roles'])
            ret['_socketAdd'] = { 'user_id': ret['user']['_id'] }

    elif route == 'emailVerify':
        ret = user_auth.emailVerify(data['email'], data['email_verification_key'])
        if ret['valid']:
            # Join (to string) any nested fields for C# typings..
            if 'roles' in ret['user']:
                # del ret['user']['roles']
                ret['user']['roles'] = ",".join(ret['user']['roles'])
            ret['_socketAdd'] = { 'user_id': ret['user']['_id'] }
    elif route == 'passwordReset':
        ret = user_auth.passwordReset(data['email'], data['password_reset_key'], data['password'])
        if ret['valid']:
            # Join (to string) any nested fields for C# typings..
            if 'roles' in ret['user']:
                # del ret['user']['roles']
                ret['user']['roles'] = ",".join(ret['user']['roles'])
            ret['_socketAdd'] = { 'user_id': ret['user']['_id'] }

    elif route == 'login':
        ret = user_auth.login(data['email'], data['password'])
        if ret['valid']:
            # Join (to string) any nested fields for C# typings..
            if 'roles' in ret['user']:
                # del ret['user']['roles']
                ret['user']['roles'] = ",".join(ret['user']['roles'])
            ret['_socketAdd'] = { 'user_id': ret['user']['_id'] }

    elif route == 'forgotPassword':
        ret = user_auth.forgotPassword(data['email'])

    elif route == 'getUserSession':
        ret = user_auth.getSession(data['user_id'], data['session_id'])
        if ret['valid']:
            # Join (to string) any nested fields for C# typings..
            if 'roles' in ret['user']:
                ret['user']['roles'] = ",".join(ret['user']['roles'])
            ret['_socketAdd'] = { 'user_id': ret['user']['_id'] }

    elif route == 'logout':
        ret = user_auth.logout(data['user_id'], data['session_id'])
        # Logout all sockets for this user.
        if '_socketSendSeparate' not in ret:
            ret['_socketSendSeparate'] = []
        ret['_socketSendSeparate'].append({
            'userIds': [ data['user_id'] ],
            'route': 'onLogout',
            'data': {
                'valid': '1',
                'msg': ''
            }
        })

        ret['_socketRemove'] = { 'user_id': data['user_id'] }

    elif route == "getImages":
        title = data['title'] if 'title' in data else ''
        url = data['url'] if 'url' in data else ''
        user_id_creator = data['user_id_creator'] if 'user_id_creator' in data else ''
        ret = _image.Get(title, url, user_id_creator, data['limit'], data['skip'])
        ret = formatRet(data, ret)
    elif route == "saveImage":
        ret = _image.Save(data['image'])
        ret = formatRet(data, ret)
    elif route == "getImageData":
        imageDataString = _file_upload.GetImageData(data['image_url'])
        ret = { 'valid': '1', 'msg': '', 'image_url': data['image_url'],
            'image_data': imageDataString }

    elif route == "saveFileData":
        if data['fileType'] == 'image':
            saveToUserImages = data['saveToUserImages'] if 'saveToUserImages' in data else False
            maxSize = data['maxSize'] if 'maxSize' in data else 600
            ret = _file_upload.SaveImageData(data['fileData'], config['web_server']['urls']['base_server'],
                maxSize = maxSize, removeOriginalFile = 1)
            if ret['valid'] and saveToUserImages and len(auth['user_id']) > 0:
                title = data['title'] if 'title' in data else ''
                if len(title) > 0:
                    userImage = { 'url': ret['url'], 'title': title, 'user_id_creator': auth['user_id'] }
                    retUserImage = _image.Save(userImage)
                    ret['userImage'] = formatRet(data, retUserImage)
        else:
            ret = _file_upload.SaveFileData(data['fileData'], config['web_server']['urls']['base_server'], data['fileName'])
    elif route == "saveImageData":
        ret = _file_upload.SaveImageData(data['fileData'], config['web_server']['urls']['base_server'], removeOriginalFile = 1)

    elif route == "getUserById":
        user = user_auth.getById(data['user_id'])
        ret['valid'] = '1'
        ret['user'] = user
        ret = formatRet(data, ret)

    elif route == 'saveBlog':
        ret = _blog.Save(data['blog'], auth['user_id'])
    elif route == 'getBlogs':
        title = data['title'] if 'title' in data else ''
        tags = data['tags'] if 'tags' in data else []
        user_id_creator = data['user_id_creator'] if 'user_id_creator' in data else ''
        slug = data['slug'] if 'slug' in data else ''
        limit = data['limit'] if 'limit' in data else 25
        skip = data['skip'] if 'skip' in data else 0
        sortKey = data['sortKey'] if 'sortKey' in data else ''
        ret = _blog.Get(title, tags, user_id_creator, slug, limit = limit, skip = skip,
            sortKey = sortKey)
    elif route == 'removeBlog':
        ret = _blog.Remove(data['id'])

    elif route == 'saveLendLibraryItem':
        ret = _lend_library.Save(data['lendLibraryItem'], auth['user_id'])
    elif route == 'getLendLibraryItems':
        title = data['title'] if 'title' in data else ''
        tags = data['tags'] if 'tags' in data else []
        userIdOwner = data['userIdOwner'] if 'userIdOwner' in data else ''
        limit = data['limit'] if 'limit' in data else 25
        skip = data['skip'] if 'skip' in data else 0
        sortKey = data['sortKey'] if 'sortKey' in data else ''
        withOwnerInfo = data['withOwnerInfo'] if 'withOwnerInfo' in data else 1
        lngLatOrigin = data['lngLatOrigin'] if 'lngLatOrigin' in data else None
        ret = _lend_library.Get(title, tags, userIdOwner, limit = limit, skip = skip,
            sortKey = sortKey, withOwnerInfo = withOwnerInfo, lngLatOrigin = lngLatOrigin)
    elif route == 'removeLendLibraryItem':
        ret = _lend_library.Remove(data['id'])

    elif route == 'saveUser':
        ret = _user.SaveUser(data['user'])

    ret['_msgId'] = msgId
    return ret

# def route1(data):
#     ret = { 'key': 'whatup route 1' }
#     return ret

# def route2(data):
#     ret = { 'hello': 'route 2' }
#     return ret

def formatRet(data, ret, arrayJoinKeys=[], arrayJoinDelimiter=","):
    stringKeys = data['string_keys'] if 'string_keys' in data else 1
    if stringKeys:
        ret = objectToStringKeys(ret, arrayJoinKeys, arrayJoinDelimiter)
    return ret

def objectToStringKeys(obj, arrayJoinKeys=[], arrayJoinDelimiter=","):
    if isinstance(obj, list):
        for item in obj:
            item = objectToStringKeys(item, arrayJoinKeys, arrayJoinDelimiter)
    elif isinstance(obj, dict):
        for key in obj:
            if isinstance(obj[key], list):
                if key in arrayJoinKeys:
                    obj[key] = arrayJoinDelimiter.join(obj[key])
                else:
                    obj[key] = objectToStringKeys(obj[key], arrayJoinKeys, arrayJoinDelimiter)
            elif isinstance(obj[key], dict):
                obj[key] = objectToStringKeys(obj[key], arrayJoinKeys, arrayJoinDelimiter)
            else:
                obj[key] = str(obj[key])
    else:
        obj = str(obj)
    return obj

def GetTimestamp():
    return int(time.time())

def AddTimestamp(ret):
    ret['timestamp'] = GetTimestamp()
    return ret
