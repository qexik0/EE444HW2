HOST = "127.0.0.1";
PORT = 6001;
global MSG_LEN;
MSG_LEN = 156;

global server_table;
server_table = int32([0 0 0 0 0 0 0 0 0 0]);

fprintf('Creating server socket...');
TCPIPServer = tcpserver(HOST, PORT, "ConnectionChangedFcn", @connectionFcn);
fprintf(' CREATED\n');


function connectionFcn(src, ~)
global MSG_LEN;
global server_table;
if src.Connected
    while true
        if src.NumBytesAvailable ~= 0
            data = read(src, MSG_LEN, "string");
            fprintf("Incoming data: %s\n", data);
            [response, server_table] = execute(server_table, data);
            fprintf("Command executed, sending back response: %s\n", response);
            response = pad(response, MSG_LEN);
            write(src, response, "string");
            fprintf("Response sent, awaiting new commands...\n");
        end
        if ~src.Connected
            return;
        end
    end
end
end

function [response, new_table] = execute(server_table, s)
s = strip(s);
tokens = split(s, ';');
op = extractBetween(tokens(1), 4, 6);
indexes = str2num(extractBetween(tokens(2), 5, strlength(tokens(2))));
data = str2num(extractBetween(tokens(3), 6, strlength(tokens(3))));
if op == "GET"
    t1 = join(string(indexes), ',');
    t2 = string(server_table(indexes + 1));
    t2 = join(t2, ',');
    response = sprintf("OP=GET;IND=%s;DATA=%s;", t1, t2);
    new_table = server_table;
elseif op == "PUT"
    for i = indexes
        server_table(i + 1) = data(i + 1);
    end
    new_table = server_table;
    fprintf("Table changed, displaying new table: \n");
    disp(new_table);
    response = "OP=PUT;IND=;DATA=;";
elseif op == "CLR"
    new_table = [0 0 0 0 0 0 0 0 0 0];
    fprintf("Table cleared, displaying new table: \n");
    disp(new_table);
    response = "OP=CLR;IND=;DATA=;";
elseif op == "ADD"
    s = 0;
    for i = indexes
        s = s + server_table(i + 1);
    end
    response = sprintf("OP=ADD;IND=;DATA=%d;", s);
    new_table = server_table;
else
    response = "";
    new_table = server_table;
    return;
end
end

