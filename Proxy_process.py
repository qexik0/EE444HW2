import socket
import time
from collections import deque

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 6001

HOST = '127.0.0.1'
PORT = 6002
MSG_LEN = 156

table = deque([[-1, 0]] * 5, maxlen=5)

def forward_to_server(message):
    while True:
        try:
            send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Socket successfully created")
            send_socket.connect((SERVER_HOST, SERVER_PORT))
            print("Successfully connected")
        except Exception as e:
            print(e)
            print("Could not establish a connection, waiting 1 second...")
            send_socket.close()
            time.sleep(1)
            continue

        while True:
            try:
                print("Sending to server")
                raw = message.ljust(MSG_LEN).encode("utf-8")
                send_socket.sendall(raw)
                left = MSG_LEN
                buf = []
                while left > 0:
                    data = send_socket.recv(left)
                    left -= len(data)
                    if len(data) == 0:  # socket closed, throw exception
                        raise Exception()
                    buf.append(data.decode("utf-8"))

                response = ''.join(buf).strip()
                print("Server responded: %s" % response)
                return response
            except KeyboardInterrupt:
                send_socket.close()
                exit(0)
            except:
                print("Connection disrupted. Trying to establish new connection")
                send_socket.close()


def execute(s):
    global table
    cmd = s.strip()
    tokens = cmd.split(';')
    op = tokens[0][3:]
    indexes = [int(x) for x in tokens[1][4:].split(',') if x]
    data = [int(x) for x in tokens[2][5:].split(',') if x]
    if op == "GET":
        missing = []
        for i in indexes:
            if i not in [x[0] for x in table]:
                missing.append(i)
        if len(missing) == 0:
            print("Request can be satisfied without server.")
            d = []
            for i in indexes:
                for j in table:
                    if j[0] == i:
                        d.append(j[1])
                        break
            return "OP=GET;IND=%s;DATA=%s;" % (','.join([str(s) for s in indexes]), ','.join([str(s) for s in d]))
        else:
            print("Data missing in cache, forwarding %s to server" % cmd)
            server_resp = forward_to_server(cmd)
            new_data = [int(x) for x in server_resp.split(';')[2][5:].split(',') if x]
            for i in missing:
                table.append([i, new_data[indexes.index(i)]])
            print("Cache changed, printing:")
            print(table)
            return server_resp
    elif op == "PUT":
        changed = False
        for i in indexes:
            for j in table:
                if j[0] == i:
                    changed = True
                    j[1] = data[indexes.index(i)]
        if changed:
            print("Updated some/all cache entries, printing:")
            print(table)
        print("Forwarding command to the server: %s" % cmd)
        server_resp = forward_to_server(cmd)
        return server_resp
    elif op == "CLR":
        table = deque([[-1, 0]] * 5, maxlen=5)
        print("Cache cleared, new_cache: ", table)
        print("Forwarding command to the server: %s" % cmd)
        server_resp = forward_to_server(cmd)
        return "OP=CLR;IND=;DATA=;"
    elif op == "ADD":
        if set(indexes).issubset(set([x[0] for x in table])):
            print("Request can be satisfied without server.")
            s = 0
            for i in table:
                if i[0] in indexes:
                    s += i[1]
            return "OP=ADD;IND=;DATA=%s;" % s
        else:
            print("Request cannot be satisfied. Forwarding to the server: %s" % cmd)
            server_resp = forward_to_server(cmd)
            return server_resp
    else:
        return ""


def handle_request(conn, addr):
    buffer = []
    left = MSG_LEN
    while left > 0:
        data = conn.recv(left)
        if len(data) == 0:
            print("Socket suddenly closed.")
            return False
        left -= len(data)
        buffer.append(data.decode("utf-8"))
    data = ''.join(buffer)
    print("Received message from the client: %s. Executing..." % data.strip())
    response = execute(data)
    print("Sending response to the client: %s" % response)
    conn.sendall(response.ljust(MSG_LEN).encode("utf-8"))
    return True


def main():
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Created socket for clients")
    listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listening_socket.bind((HOST, PORT))
    print("Socket is bound to IP:", HOST, " PORT:", PORT)
    listening_socket.listen(1)
    print("Listening for clients")
    while True:
        try:
            conn, clientAddress = listening_socket.accept()
            print('Connected ', clientAddress)
            while handle_request(conn, clientAddress):
                continue
        except KeyboardInterrupt:
            listening_socket.shutdown(2)
            listening_socket.close()
        except:
            continue


if __name__ == "__main__":
    main()

