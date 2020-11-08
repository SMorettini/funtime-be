# *********************************************************************

import json
import logging
import random

logging.basicConfig()

logging.getLogger().setLevel(logging.INFO)

# *********************************************************************

# Maps room IDs to Game objects.
ROOMS = {}

# map websockets to games
USERS = {}

# Need to keep in sync with /frontend/public/img/*.
IMAGE_NAMES = ['dance.png', 'eagle.png', 'garland.png', 'gate.png', 'half-moon.png', 'parivrtta-trikonasana.png', 'vrksasana.png', 
'warrior-I.png', 'warrior-II.png', 'bigtoepose.jpg', 'chairpose.jpg']

class Player:
    def __init__(self, receive, send, game, name):
        self.receive = receive
        self.send = send
        self.game = game
        self.round_scores = []
        self.name = name
        self.ready = False
    
    async def send(self, data):
        await self.send({
            'type': 'websocket.send',
            'text': json.dumps(data)
        })

class Game:
    def __init__(self, room):
        self.room = room
        self.total_rounds = 7 # maybe change later
        self.current_round = 0
        # map websocket to player objects
        self.players = {} 

        self.used_images = set()

    def add_player(self, receive, send, name):
        player = Player(receive, send, self, name)
        self.players[name] = player

        logging.info('added player {} to game in room {}'.format(player.name, self.room))
    
    async def remove_player(self, name):
        if name not in self.players:
            return
        logging.info('removed player {} from game in room {}'.format(self.players[name].name, self.room))
        self.players.pop(name)

        if len(self.players) == 0:
            await self.end()
    
    def get_scores(self):
        return {
            player.name: player.round_scores for player in self.players.values()
        }
    
    async def ready_player(self, name):
        self.players[name].ready = True

        logging.info('player {} ready for room {}'.format(self.players[name].name, self.room))

        if sum([p.ready for p in self.players.values()]) == len(self.players):
            await self.start_round()
    
    async def start_round(self):

        logging.info('starting round {} in room {}'.format(self.current_round, self.room))

        image = random.choice(IMAGE_NAMES)
        while image in self.used_images:
            image = random.choice(IMAGE_NAMES)

        duration = random.randint(10, 20), # TODO: tune duration?
        self.used_images.add(image)
        
        await self.notify_players({
            'action': 'START_ROUND',
            'roundDuration': duration,
            'imageName': image,
            'currentRound': self.current_round,
            'totalRounds': self.total_rounds,
            'prevScores': self.get_scores(),
        })
    
    async def send_score(self, name, score):
        player = self.players[name]
        player.round_scores.append(score)

        logging.info('player {} sending in score to room {}'.format(player.name, self.room))

        # if all scores are in, start next round
        if sum(len(p.round_scores) == self.current_round + 1 for p in self.players.values()) == len(self.players):
            self.current_round += 1
            if self.current_round == self.total_rounds:
                await self.end()
            else:
                await self.start_round()
    
    async def end(self):

        logging.info('game ending in room {}'.format(self.room))

        await self.notify_players({
            'action': 'END_GAME',
            'totalRounds': self.total_rounds,
            'prevScores': self.get_scores(),
        })
        ROOMS.pop(self.room)

    async def notify_players(self, data):
        for _, player in self.players.items():
            await player.send({
                'type': 'websocket.send',
                'text': json.dumps(data)
            })

# *********************************************************************

async def join_or_create_game(receive, send, room, name):
    ROOMS.setdefault(room, Game(room))
    game = ROOMS[room]
    USERS[name] = game
    game.add_player(receive, send, name)

# *********************************************************************

async def websocket_application(scope, receive, send):
    while True:
        event = await receive()

        if event['type'] == 'websocket.connect':
            await send({
                'type': 'websocket.accept'
            })

        if event['type'] == 'websocket.disconnect':
            break

        if event['type'] == 'websocket.receive':
            data = json.loads(event['text'])

            if "action" not in data:
                logging.error("no action: {}".format(data))
                continue

            if data["action"] == "JOIN_GAME":
                room = data['room']
                name = data['name']
                await join_or_create_game(receive, send, room, name)
            elif data["action"] == "SET_READY":
                room = data['room']
                name = data['name']
                if room not in ROOMS:
                    logging.error("no game in room: {}".format(data))
                    continue
                game = ROOMS[room]
                await game.ready_player(name)
            elif data["action"] == "FINISH_ROUND":
                room = data['room']
                name = data['name']
                if room not in ROOMS:
                    logging.error("no game in room: {}".format(data))
                    continue
                game = ROOMS[room]
                score = data['score']
                await game.send_score(name, score)
            else:
                logging.error("unsupported event: {}".format(data))