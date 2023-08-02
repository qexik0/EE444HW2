import socket
from ctypes import c_int32
import time

HOST = '127.0.0.1'
PORT = 6002
MSG_LEN = 156


def input_indexes():
    while True:
        print("Please provide indexes in range [0; 9] as space-separated list.")
        try:
            ind = [int(x) for x in input().split()]
        except ValueError:
            print("Error parsing the string")
            continue
        if not all([0 <= x < 10 for x in ind]):
            print("Incorrect indexes")
            continue
        if len(ind) != len(set(ind)):
            print("Repeating indexes are forbidden")
            continue
        break
    return ind


def input_data(n):
    while True:
        print("Please provide %d numbers as space-separated list. Note, that numbers will be truncated to 32 bits" % n)
        try:
            vals = [int(x) for x in input().split()]
        except ValueError:
            print("Error parsing the string")
            continue
        if len(vals) != n:
            print("Number of data does not match the number of indexes")
            continue
        data = [c_int32(x).value for x in vals]
        break
    return data


def create_message():
    d = {0: "GET", 1: "PUT", 2: "CLR", 3: "ADD"}
    while True:
        print("Please provide an operation code as a single number: GET - 0; PUT - 1; CLR - 2; ADD - 3;")
        try:
            opcode = int(input())
        except ValueError:
            print("Error parsing the number")
            continue
        if opcode not in d.keys():
            print("Wrong opcode!")
            continue
        break

    op = "OP=%s;" % d[opcode]
    if d[opcode] == "GET" or d[opcode] == "ADD":
        ind = input_indexes()
        indexes = "IND=%s;" % ','.join([str(s) for s in ind])
        data = "DATA=;"
    elif d[opcode] == "PUT":
        ind = input_indexes()
        vals = input_data(len(ind))
        indexes = "IND=%s;" % ','.join([str(s) for s in ind])
        data = "DATA=%s;" % ','.join([str(s) for s in vals])
    elif d[opcode] == "CLR":
        indexes = "IND=;"
        data = "DATA=;"
    return op + indexes + data


def main():
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))
            print("Socket successfully created and connected")
        except:
            print("Could not establish a connection, waiting 1 second...")
            client_socket.close()
            time.sleep(1)
            continue

        while True:
            try:
                x = create_message()
                print("Resulting message: %s. Sending it to server..." % x)
                raw = x.ljust(MSG_LEN).encode("utf-8")
                client_socket.sendall(raw)
                print("Message sent, receiving the response...")
                left = MSG_LEN
                buf = []
                while left > 0:
                    data = client_socket.recv(left)
                    left -= len(data)
                    if len(data) == 0:  # socket closed, throw exception
                        raise Exception()
                    buf.append(data.decode("utf-8"))

                response = ''.join(buf).strip()
                print("Server responded: %s. Creating message again." % response)
            except KeyboardInterrupt:
                client_socket.close()
                exit(0)
            except:
                print("Connection disrupted. Trying to establish new connection")
                client_socket.close()
                break


if __name__ == "__main__":
    main()

