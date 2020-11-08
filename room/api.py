from django.shortcuts import render
from django.http import HttpResponse

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant
from twilio.rest import Client
import random
from time import sleep
import os


ACCOUNT_SID = 'AC6a24a563a2ca6359406285f0126777d6'
AUTH_TOKEN = '55706a6a8c2903bcd27066e0991e1cc1'
API_KEY_SID = 'SKd5aa7fa8b8fdd9fb57ef6da0bbb0739d'
API_KEY_SECRET = 'XpbmyqBwqRo7T6uSuImprpEorJSsd6hx'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

NAME_WORDS = [
    ['exuberant', 'restless', 'energetic', 'eager', 'infected', 'quarantined'], # adjectives
    ['yogi', 'poser', 'hacker', 'millenial', 'boomer', 'guru', 'student'], # nouns
]


def createRoom(request, name):
    room = client.video.rooms.create(
                                type='peer-to-peer',
                                unique_name=name
                            )
    print(room.sid) # cannot make a room with the same name
    return HttpResponse(room.sid)


def joinRoom(request, name):
    room = client.video.rooms(name).fetch()
    return HttpResponse(room.unique_name)


def completeRoom(request, name):
    room = client.video.rooms(name).update(status='completed')
    return HttpResponse(room.unique_name)


def workflow(request, name):
    createRoom(name)
    joinRoom(name)
    sleep(5)
    return HttpResponse(completeRoom(name))


def getToken(request, room):
    # Create an Access Token
    token = AccessToken(ACCOUNT_SID, API_KEY_SID, API_KEY_SECRET)

    username = '-'.join(random.choice(NAME_WORDS[i]) for i in range(2))
    # Set the Identity of this token
    token.identity = username

    # Grant access to Video
    grant = VideoGrant(room=room) # this must be here
    token.add_grant(grant)

    # Serialize the token as a JWT
    jwt = token.to_jwt()

    return HttpResponse(jwt)