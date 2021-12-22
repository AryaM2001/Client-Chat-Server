import socket
import os
import signal
import sys
import selectors

# Selector for helping us select incoming data and connections from multiple sources.

sel = selectors.DefaultSelector()

# Client list for mapping connected clients to their connections.

client_list = []

user_dict = {} # dictionary that takes the users name as a key and list of the followed term as the values


# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message = 'DISCONNECT CHAT/1.0\n'
    for reg in client_list:
        reg[1].send(message.encode())
    sys.exit(0)

# function that will remove punctuation form a message
def removePunc (message):
    punctuation = '''!()-[]{};:'"\,<>./?#$%^&*_~'''

    # if the character is in the punctuation list then remove it from the message
    for char in message:
        if char in punctuation:
            message = message.replace(char, "")

    return message # return the message with the removed the punctuation


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

def get_line_from_socket(sock):
    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line


# Search the client list for a particular user.

def client_search(user):
    for reg in client_list:
        if reg[0] == user:
            return reg[1]
    return None


# Search the client list for a particular user by their socket.

def client_search_by_socket(sock):
    for reg in client_list:
        if reg[1] == sock:
            return reg[0]
    return None


# Add a user to the client list.

def client_add(user, conn):
    registration = (user, conn)
    client_list.append(registration)


# Remove a client when disconnected.

def client_remove(user):
    for reg in client_list:
        if reg[0] == user:
            client_list.remove(reg)
            break

# function that will execute the list command. List all the users connected to the server
def list(user):
    namesList = []

    # for loop that adds all the client names to the nameList
    for reg in client_list:
        namesList.append(reg[0])

    namesList = sorted(namesList) #sort th names in alphabetic order
    names = namesList[0]

    i = 1

    # while loop that gets all the names and adds them to a string
    while (i < len(namesList)):
        names = names + ", " + namesList[i]
        i = i + 1

    # for loop that sends the names string to the user who listed the command
    for reg in client_list:
        if reg[0] == user:
            client_sock = reg[1]
            forwarded_message = f'{names}\n'
            client_sock.send(forwarded_message.encode())

# function that will execute the follow command. Adds term user wants to follow to their follow list
def Follow (user, words):

    # check and see if there was multiple words entered
    if len(words) > 3:
        sendMess = "Please enter a term to follow"

        # notify the user who wanted to follow multiple terms
        for reg in client_list:
            if reg[0] == user:
                client_sock = reg[1]
                forwarded_message = f'{sendMess}\n'
                client_sock.send(forwarded_message.encode())

    #check and see if  there was no word entered
    elif len(words) < 3:
        sendMess = "Please enter a single term to follow"

        # notify the user who wanted to follow single terms
        for reg in client_list:
            if reg[0] == user:
                client_sock = reg[1]
                forwarded_message = f'{sendMess}\n'
                client_sock.send(forwarded_message.encode())

    else:
        list = user_dict.get(user)

        # check and see if the user already follows the term they want to follow
        if words[2] in list:
            sendMess = "You already follow this term "

            # Notify the user they already follow this term
            for reg in client_list:
                if reg[0] == user:
                    client_sock = reg[1]
                    forwarded_message = f'{sendMess}\n'
                    client_sock.send(forwarded_message.encode())

        else:
            follow_term = words[2]
            user_dict[user].append(follow_term) # add the term to values list in the user dictionary

            sendMess = "You followed " + follow_term

            # Notify the user they followed this term

            for reg in client_list:
                if reg[0] == user:
                    client_sock = reg[1]
                    forwarded_message = f'{sendMess}\n'
                    client_sock.send(forwarded_message.encode())

# function that will execute the unfollow command. Unadds term user wants to unfollow from their follow list
def unfollow(user, words):

    #check and see if there was no word entered
    if len(words) < 3:
        sendMess = "Please enter a term to unfollow"

        # notify the user who wanted to follow multiple terms
        for reg in client_list:
            if reg[0] == user:
                client_sock = reg[1]
                forwarded_message = f'{sendMess}\n'
                client_sock.send(forwarded_message.encode())

    # check and see if there was multiple words entered
    elif len(words) > 3:
        sendMess = "Please enter a single term to unfollow"

        # notify the user who wanted to follow multiple terms
        for reg in client_list:
            if reg[0] == user:
                client_sock = reg[1]
                forwarded_message = f'{sendMess}\n'
                client_sock.send(forwarded_message.encode())

    # Check and see if the words entered is @all or the users name
    elif words[2] == "@all" or words[2] == "@"+user:
        sendMess = "Cant unfollow this term"

        # notify the user they cant unfollow these terms
        for reg in client_list:
            if reg[0] == user:
                client_sock = reg[1]
                forwarded_message = f'{sendMess}\n'
                client_sock.send(forwarded_message.encode())


    else:
        list = user_dict.get(user)

        # check and see if the user already follows the term they want to unfollow
        if words[2] not in list:
            sendMess = "You have not followed this term yet... Cant unfollow"

            # if they dont follow the term let the user know they cant unfollow term
            for reg in client_list:
                if reg[0] == user:
                    client_sock = reg[1]
                    forwarded_message = f'{sendMess}\n'
                    client_sock.send(forwarded_message.encode())

        else:
            follow_term = words[2]
            user_dict[user].remove(follow_term) # remove the term from values list in the user dictionary

            sendMess = "You unfollowed " + follow_term

            # notify the user they unfollowed the terms
            for reg in client_list:
                if reg[0] == user:
                    client_sock = reg[1]
                    forwarded_message = f'{sendMess}\n'
                    client_sock.send(forwarded_message.encode())

# function that will list the terms followed by the user
def followingTerms(user):
    follow_list = user_dict.get(user) # get the terms followed by the given user
    follow_list = sorted(follow_list)

    follow = follow_list[0]

    i = 1

    # while loop that gets all the followed terms from the user and adds them to a string
    while (i < len(follow_list)):
        follow = follow + ", " + follow_list[i]
        i = i + 1

    # send following terms string to the user who requestd it
    for reg in client_list:
        if reg[0] == user:
            client_sock = reg[1]
            forwarded_message = f'{follow}\n'
            client_sock.send(forwarded_message.encode())

# Function to send files to clients.
def attach(sentMess, sock):

    # get the filename and the user who sent it
    filename = sentMess[2]
    userSent = sentMess[0]

    list = []

    # remove the punction from any words passed
    for element in sentMess:
        word = removePunc(element)
        list.append(word)


    #get the filename sent to the user
    if os.path.isfile(filename):

        size = os.path.getsize(filename) #get the size of the file passed
        fileSize = str(size)
        fileInfo = filename + " " + fileSize + " " + userSent #combine filename, file size and user names in one stirng
        fileInfo_Size = len(fileInfo) # get the length of the file infor to pass to clients latter

        #open the file and store the first 1024 bytes
        with open(filename, "rb") as file:

            bytes = file.read(1024)

            #for loop that will send messages to each client
            for client in client_list:

                name = "@" + client[0] + ":"

                #check to see if current client is the one who sent the message
                if name == sentMess[0]:

                    #if the current client is the one who sent the file then send the following message
                    message = "Attachment " + filename + " attached and distributed"
                    forwarded_message = f'{message}\n'
                    sock.send(forwarded_message.encode())

                #executes if the current client is not the one who sent the file
                else:

                    # for loop to check and see if the client follows any of the terms that were sent. if the do follow a term then send that client the file
                    for term in list:
                        if term in user_dict[client[0]]:
                            client_sock = client[1]
                            message = "FILE" # first send FILE message to alert the client that a file is coming
                            forwarded_message = f'{message} {str(fileInfo_Size)}\n' # send the information about the file size first
                            client_sock.send(forwarded_message.encode())
                            client_sock.send(fileInfo.encode()) # send information about the file

                            client_sock.send(bytes) # send first 1024 bytes to the clietn

                            flag = True;
                            check = 1024

                            # while loop that will send the remaining bytes in the file to the client
                            while flag == True:

                                # if check > 1024:
                                bytes = file.read(1024);
                                client_sock.send(bytes)
                                check = check + 1024

                                # if the check variable is bigger then the file size, then we have sent the entire file, and its time ot break the loop
                                if (check > size):
                                    flag = False



                            print("file sent")
                            break

    # else statement for when the file does not exist
    else:
        message = 'Error File does not exist' #send error message to the client who attempted to send the file
        forwarded_message = f'{message}\n'
        sock.send(forwarded_message.encode())


def read_message(sock, mask):
    message = get_line_from_socket(sock)

    if message == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()

    # Receive the message.  

    else:
        user = client_search_by_socket(sock)
        print(f'Received message from user {user}:  ' + message)
        words = message.split(' ')


        # Check for client disconnections.  

        if words[0] == 'DISCONNECT':
            print('Disconnecting user ' + user)
            client_remove(user)
            sel.unregister(sock)
            sock.close()

        # !executes the exit command, will disconnect the user from the server
        elif words[1] == '!exit':
            print('Disconnecting user ' + user)
            message = "DISCONNECT"

            #send the DISCONNECT message to the client who entered the exit command
            for reg in client_list:
                if reg[0] == user:
                    client_sock = reg[1]
                    forwarded_message = f'{message}\n'
                    client_sock.send(forwarded_message.encode())

            #remove the user, its socket and close it
            client_remove(user)
            sel.unregister(sock)
            sock.close()

        # if user is enters !list command
        elif words[1] == '!list':
            list(user)

        # if user is enters !follow? command
        elif words[1] == "!follow?":
            followingTerms(user)

        # if user is enters !follow command
        elif words[1] == "!follow":
            Follow(user, words)

        # if user is enters !unfollow command
        elif words[1] == "!unfollow":
            unfollow(user, words)

        # if user is enters !attach command
        elif words[1] == "!attach":
            attach(words, sock) # pass the broken down message and the socket of the user

        # if the user enters a text that does not contain a command
        else:

            # remove punctuation from the message and split it at spaces
            stripedMessage = removePunc(message)
            stripedWords = stripedMessage.split(' ')

            #go through each client
            for client in client_list:

                #if the name is not same as the user who entered text continue
                name = "@" + client[0]
                if name != stripedWords[0]:
                    for term in stripedWords: # go through each term in the stripped words
                        if term in user_dict[client[0]]: # check and see if the term is a followed term by ther user, if it is then send the message to that user
                            client_sock = client[1]
                            forwarded_message = f'{message}\n'
                            client_sock.send(forwarded_message.encode())
                            break







# Function to accept and set up clients.

def accept_client(sock, mask):
    conn, addr = sock.accept()
    print('Accepted connection from client address:', addr)
    message = get_line_from_socket(conn)
    message_parts = message.split()

    # Check format of request.

    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0')):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')
        response = '400 Invalid registration\n'
        conn.send(response.encode())
        conn.close()

    # If request is properly formatted and user not already listed, go ahead with registration.

    else:
        user = message_parts[1]

        if (client_search(user) == None):
            client_add(user, conn)
            print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')
            name = user
            user_dict[user] = ["@"+name, "@all"] # when the user connects add there name as a key and their name and all as values in the list
            response = '200 Registration succesful\n'
            conn.send(response.encode())
            conn.setblocking(False)
            sel.register(conn, selectors.EVENT_READ, read_message)

        # If user already in list, return a registration error.

        else:
            print('Error:  Client already registered.')
            print('Connection closing ...')
            response = '401 Client already registered\n'
            conn.send(response.encode())
            conn.close()


# Our main function.

def main():
    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(100)
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, accept_client)
    print('Waiting for incoming client connections ...')

    # Keep the server running forever, waiting for connections or messages.

    while (True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)


if __name__ == '__main__':
    main()

