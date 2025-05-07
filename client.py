import socket
from shmessage import shmessage, WAVEREQ
from shpdu import shpdu
import threading

game_started = False

def receive_loop(pdusock):
    global game_started
    while True:
        try:
            response = pdusock.recvMessage()
            t = response.getType()
            if t == WAVEREQ.CHAT:
                print(f"\n[{response.getValue('from')}]: {response.getValue('text')}")
            elif t == WAVEREQ.STRT:
                print(f"\n[GAME STATUS]: {response.getValue('text')}")
                game_started = True
            elif t == WAVEREQ.CARD:
                if response.getValue("error"):
                    print(response.getValue("error"))
                elif response.getValue("topic"):
                    print("\nCard Drawn:")
                    print(f"Topic: {response.getValue('topic')}")
                    print(f"{response.getValue('left')}  \u2194  {response.getValue('right')}")
                    print(f"Psychic: {response.getValue('psychic')}")
                elif response.getValue("target_start"):
                    print("\n[Private Info] Target Range:", response.getValue("target_start"), "-", response.getValue("target_end"))
            elif t == WAVEREQ.CLUE:
                if response.getValue("error"):
                    print(response.getValue("error"))
                else:
                    print(f"\n[Clue Submitted]: {response.getValue('clue')}")
            elif t == WAVEREQ.GUESS:
                if response.getValue("error"):
                    print(response.getValue("error"))
                else:
                    print("\n[Guess Confirmed]")
            elif t == WAVEREQ.SCRB:
                print("\nScore Update")
                for k in ['team_guess', 'target_range', 'target_center', 'points', 'TeamA', 'TeamB']:
                    val = response.getValue(k)
                    if val:
                        print(f"{k}: {val}")
            elif t == WAVEREQ.ENDG:
                print("\n\U0001F3C1 Game Over")
                print(f"Winner: {response.getValue('winner')}")
                game_started = False
                break
        except:
            break

def main():
    global game_started
    host = input("Enter host: ")
    port = int(input("Enter port: "))
    username = input("Enter your username: ")

    while True:
        with socket.socket() as s:
            s.connect((host, port))
            pdusock = shpdu(s)

            while True:
                action = input("\nEnter request type (CRE8, JOIN, GLST, or EXIT): ").strip().upper()

                if action == "EXIT":
                    print("Exiting client...")
                    return

                if action not in WAVEREQ.__members__:
                    print("Invalid request type.")
                    continue

                msg = shmessage()

                if action in ["CRE8", "JOIN"]:
                    msg.setType(WAVEREQ[action])
                    msg.addValue("game_name", input("Enter game name: "))
                    msg.addValue("pin", input("Enter 4-digit game PIN: "))
                    msg.addValue("username", username)

                elif action == "GLST":
                    msg.setType(WAVEREQ.GLST)

                pdusock.sendMessage(msg)
                response = pdusock.recvMessage()

                print("Response Type:", response.getType().name)
                print("Status:", response.getValue("status"))

                if response.getType() == WAVEREQ.GLST:
                    print("Available Games:", response.getValue("games"))

                if action in ["CRE8", "JOIN"] and response.getValue("status") == "Success":
                    game_id = response.getValue("game_id")
                    print("Game ID:", game_id)
                    print("You've entered the game lobby. Type CHAT or STRT to begin.")

                    game_started = False
                    threading.Thread(target=receive_loop, args=(pdusock,), daemon=True).start()

                    while not game_started:
                        cmd = input("Enter pre-start command (CHAT, STRT, EXIT): ").strip().upper()
                        if cmd == "EXIT":
                            return
                        elif cmd == "CHAT":
                            text = input("What would you like to send: ")
                            chat_msg = shmessage()
                            chat_msg.setType(WAVEREQ.CHAT)
                            chat_msg.addValue("game_id", game_id)
                            chat_msg.addValue("username", username)
                            chat_msg.addValue("text", text)
                            pdusock.sendMessage(chat_msg)
                        elif cmd == "STRT":
                            start_msg = shmessage()
                            start_msg.setType(WAVEREQ.STRT)
                            start_msg.addValue("game_id", game_id)
                            pdusock.sendMessage(start_msg)
                        else:
                            print("Invalid command. Only CHAT, STRT, or EXIT allowed before game starts.")

                    while game_started:
                        cmd = input("Enter in-game command (CHAT, CARD, CLUE, GUESS, SCRB, ENDG, EXIT): ").strip().upper()

                        if cmd == "EXIT":
                            break
                        elif cmd == "CHAT":
                            text = input("What would you like to send: ")
                            chat_msg = shmessage()
                            chat_msg.setType(WAVEREQ.CHAT)
                            chat_msg.addValue("game_id", game_id)
                            chat_msg.addValue("username", username)
                            chat_msg.addValue("text", text)
                            pdusock.sendMessage(chat_msg)
                        elif cmd == "CARD":
                            card_msg = shmessage()
                            card_msg.setType(WAVEREQ.CARD)
                            card_msg.addValue("game_id", game_id)
                            card_msg.addValue("username", username)
                            pdusock.sendMessage(card_msg)
                        elif cmd == "CLUE":
                            clue = input("Enter clue: ")
                            clue_msg = shmessage()
                            clue_msg.setType(WAVEREQ.CLUE)
                            clue_msg.addValue("game_id", game_id)
                            clue_msg.addValue("clue", clue)
                            clue_msg.addValue("psychic", username)
                            pdusock.sendMessage(clue_msg)
                        elif cmd == "GUESS":
                            value = input("Enter guess (1-20): ")
                            guess_msg = shmessage()
                            guess_msg.setType(WAVEREQ.GUESS)
                            guess_msg.addValue("game_id", game_id)
                            guess_msg.addValue("username", username)
                            guess_msg.addValue("value", value)
                            pdusock.sendMessage(guess_msg)
                        elif cmd == "SCRB":
                            score_msg = shmessage()
                            score_msg.setType(WAVEREQ.SCRB)
                            score_msg.addValue("game_id", game_id)
                            pdusock.sendMessage(score_msg)
                        elif cmd == "ENDG":
                            end_msg = shmessage()
                            end_msg.setType(WAVEREQ.ENDG)
                            end_msg.addValue("game_id", game_id)
                            pdusock.sendMessage(end_msg)
                        else:
                            print("Invalid command.")

if __name__ == "__main__":
    main()
