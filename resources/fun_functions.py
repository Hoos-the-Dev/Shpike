
import random

class TicTacToe:

    player1 = ''
    player2 = ''
    turn = ''
    count = 0

    winning_conditions = [
        [0,1,2],
        [3,4,5],
        [6,7,8],
        [1,4,7],
        [2,5,8],
        [0,4,8],
        [2,4,6]
    ]

    board = []

    Games = {}

    def check_gameOver(channel_id, p1, p2):
        """Check to see if theres an active game"""
        if channel_id and p1 and p2 in TicTacToe.Games:
            return True
        else:
            return False

    async def create_game(ctx, channel_id, p1, p2):

        global player1
        global player2
        global turn
        global gameOver
        global count

        if gameOver == True:
            global board
            board = [":white_large_square:",":white_large_square:",":white_large_square:",
                    ":white_large_square:",":white_large_square:",":white_large_square:",
                    ":white_large_square:",":white_large_square:",":white_large_square:"]
            turn = ""
            player1 = p1.id
            player2 = p2.id


            line = ""
            for x in range(len(board)):
                if x == 2 or x == 5 or x == 8:
                    line += " " + board[x]
                    await ctx.send(line)
                    line = ""
                else:
                    line += " " + board[x]

            # determine who goes first
            num = random.randint(1,2)
            if num == 1:
                turn == player1
                await ctx.send(f"It's {p1.mention}'s turn")
            elif num == 2:
                turn == player2
                await ctx.send(f"It's {p2.mention}'s turn")

        else:
            await ctx.send("homie are you rage quitting? finish that game")
        player1 = TicTacToe.player1
        player2 = TicTacToe.player2
        turn = TicTacToe.turn
        gameOver = TicTacToe.check_gameOver(channel_id, p1, p2)


                    
        
        
