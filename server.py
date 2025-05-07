import socket
import threading
from model import GameManager
from shmessage import shmessage, WAVEREQ
from shpdu import shpdu

HOST = 'localhost'
PORT = 50000
game_manager = GameManager()
clients = []

def broadcast_to_game(game_id, message):
    for sock, gid, _ in clients:
        if gid == game_id:
            try:
                shpdu(sock).sendMessage(message)
            except Exception:
                pass

def send_to_user(username, game_id, message):
    for sock, gid, user in clients:
        if gid == game_id and user == username:
            try:
                shpdu(sock).sendMessage(message)
            except Exception:
                pass

def handle_client(csoc):
    pdusock = shpdu(csoc)
    game_id = None
    username = None

    try:
        while True:
            try:
                msg = pdusock.recvMessage()
            except ConnectionResetError:
                break

            req_type = msg.getType()
            response = shmessage()

            if req_type == WAVEREQ.CRE8:
                game = game_manager.create_game(
                    msg.getValue('game_name'),
                    msg.getValue('pin'),
                    msg.getValue('username')
                )
                response.setType(WAVEREQ.CRE8)
                response.addValue('status', 'Success' if game else 'Failure')
                if game:
                    game_id = game.game_id
                    username = msg.getValue('username')
                    response.addValue('game_id', game_id)
                    clients.append((csoc, game_id, username))

            elif req_type == WAVEREQ.JOIN:
                game = game_manager.join_game(
                    msg.getValue('game_name'),
                    msg.getValue('pin'),
                    msg.getValue('username')
                )
                response.setType(WAVEREQ.JOIN)
                response.addValue('status', 'Success' if game else 'Failure')
                if game:
                    game_id = game.game_id
                    username = msg.getValue('username')
                    response.addValue('game_id', game_id)
                    clients.append((csoc, game_id, username))

            elif req_type == WAVEREQ.GLST:
                response.setType(WAVEREQ.GLST)
                games = game_manager.list_games()
                response.addValue("status", "Success")
                response.addValue("games", ", ".join(games) if games else "No available games")

            elif req_type == WAVEREQ.CHAT:
                game_id = msg.getValue("game_id")
                username = msg.getValue("username")
                text = msg.getValue("text")
                response.setType(WAVEREQ.CHAT)
                response.addValue("from", username)
                response.addValue("text", text)
                broadcast_to_game(game_id, response)
                continue

            elif req_type == WAVEREQ.STRT:
                game_id = msg.getValue("game_id")
                game = game_manager.get_game_by_id(game_id)
                response.setType(WAVEREQ.STRT)

                if game:
                    try:
                        game.start_game()
                        players = game.players
                        if len(players) != 4:
                            response.addValue("status", "Failure")
                            response.addValue("reason", "Exactly 4 players required to start the game.")
                        else:
                            teamA = [p.username for p in players if p.team == "TeamA"]
                            teamB = [p.username for p in players if p.team == "TeamB"]
                            teamA_str = " and ".join(teamA)
                            teamB_str = " and ".join(teamB)

                            game.round_number = 1
                            psychic = game.assign_psychic()
                            psychic_player = next(p for p in players if p.username == psychic)
                            guesser = [p.username for p in players if p.team == psychic_player.team and not p.is_psychic][0]

                            announce = shmessage()
                            announce.setType(WAVEREQ.STRT)
                            announce.addValue("text", f"Teams set. TeamA: {teamA_str} | TeamB: {teamB_str}\nRound 1: {psychic_player.team}'s turn. Psychic is {psychic}, guesser is {guesser}")
                            broadcast_to_game(game_id, announce)
                            continue
                    except Exception as e:
                        response.addValue("status", "Failure")
                        response.addValue("reason", str(e))
                else:
                    response.addValue("status", "Failure")
                    response.addValue("reason", "Game not found")

            elif req_type == WAVEREQ.CARD:
                game = game_manager.get_game_by_id(msg.getValue("game_id"))
                username = msg.getValue("username")
                if game:
                    psychic = next((p for p in game.players if p.username == username), None)
                    if not psychic or not psychic.is_psychic:
                        warn = shmessage()
                        warn.setType(WAVEREQ.CARD)
                        warn.addValue("error", "Only the psychic can draw the card.")
                        send_to_user(username, game.game_id, warn)
                        continue
                    card = game.draw_card()
                    if card:
                        pub = shmessage()
                        pub.setType(WAVEREQ.CARD)
                        pub.addValue("topic", card.topic)
                        pub.addValue("left", card.left_hint)
                        pub.addValue("right", card.right_hint)
                        pub.addValue("psychic", username)
                        broadcast_to_game(game.game_id, pub)

                        secret = shmessage()
                        secret.setType(WAVEREQ.CARD)
                        secret.addValue("target_start", str(card.target_start))
                        secret.addValue("target_end", str(card.target_end))
                        send_to_user(username, game.game_id, secret)
                    continue

            elif req_type == WAVEREQ.CLUE:
                game = game_manager.get_game_by_id(msg.getValue("game_id"))
                psychic = msg.getValue("psychic")
                if game:
                    player = next((p for p in game.players if p.username == psychic), None)
                    if not player or not player.is_psychic:
                        warn = shmessage()
                        warn.setType(WAVEREQ.CLUE)
                        warn.addValue("error", "\n Only the psychic can submit a clue.")
                        send_to_user(psychic, game.game_id, warn)
                        continue
                    clue = msg.getValue("clue")
                    game.submit_clue(clue, psychic)
                    clue_msg = shmessage()
                    clue_msg.setType(WAVEREQ.CLUE)
                    clue_msg.addValue("clue", clue)
                    broadcast_to_game(game.game_id, clue_msg)
                    continue

            elif req_type == WAVEREQ.GUESS:
                game = game_manager.get_game_by_id(msg.getValue("game_id"))
                username = msg.getValue("username")
                if game:
                    psychic_player = next(p for p in game.players if p.is_psychic)
                    team = psychic_player.team
                    guesser = next(p for p in game.players if p.team == team and not p.is_psychic)
                    if username != guesser.username:
                        warn = shmessage()
                        warn.setType(WAVEREQ.GUESS)
                        warn.addValue("error", "Only the guesser can submit a guess.")
                        send_to_user(username, game.game_id, warn)
                        continue

                    value = int(msg.getValue("value"))
                    game.submit_guess(team, value)

                    result = game.evaluate_guess()
                    if result:
                        score_msg = shmessage()
                        score_msg.setType(WAVEREQ.SCRB)
                        for k, v in result.items():
                            score_msg.addValue(k, str(v))
                        broadcast_to_game(game.game_id, score_msg)

                    winner = game.check_winner()
                    if winner:
                        end = shmessage()
                        end.setType(WAVEREQ.ENDG)
                        end.addValue("winner", winner)
                        broadcast_to_game(game.game_id, end)

                        continue

                    game.next_round()
                    new_psychic = game.assign_psychic()
                    psychic_player = next(p for p in game.players if p.username == new_psychic)
                    new_guesser = [p.username for p in game.players if p.team == psychic_player.team and not p.is_psychic][0]
                    round_msg = shmessage()
                    round_msg.setType(WAVEREQ.STRT)
                    round_msg.addValue("text", f"Next round! {psychic_player.team}'s turn. Psychic is {new_psychic}, guesser is {new_guesser}")
                    broadcast_to_game(game.game_id, round_msg)
                    continue

            elif req_type == WAVEREQ.SCRB:
                game = game_manager.get_game_by_id(msg.getValue("game_id"))
                if game:
                    response.setType(WAVEREQ.SCRB)
                    response.addValue("TeamA", str(game.scores["TeamA"]))
                    response.addValue("TeamB", str(game.scores["TeamB"]))
                    pdusock.sendMessage(response)
                    continue

            elif req_type == WAVEREQ.ENDG:
                game = game_manager.get_game_by_id(msg.getValue("game_id"))
                response.setType(WAVEREQ.ENDG)
                if game:
                    winner = game.check_winner()
                    response.addValue("winner", winner if winner else "No winner yet")
                    broadcast_to_game(game.game_id, response)
                    continue

            pdusock.sendMessage(response)

    except Exception:
        pass
    finally:
        pdusock.close()
        if (csoc, game_id, username) in clients:
            clients.remove((csoc, game_id, username))
            print(f"Client {username} disconnected.") 


def run_server():
    with socket.socket() as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            csoc, addr = s.accept()
            print(f"Client connected from {addr}")
            threading.Thread(target=handle_client, args=(csoc,), daemon=True).start()

if __name__ == "__main__":
    run_server()