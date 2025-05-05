from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "ALJSD"
socketio = SocketIO(app)

# biblioteca ue vai guardar os códigos das salas criadas
rooms = {} 

def generate_uni_code(Length):
    while True:
        code = ""
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code


@app.route("/", methods = ["POST", "GET"])
def home():
    session.clear() #limpando sessão
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("homepage.html", error="Insira um nome", code=code, name=name)
        
        #VERIRICAÇÃO PARA ELE INSERIR O NÚMERO DE UMA SALA
        if join != False and not code:
           return render_template("homepage.html", error="Insira o código de uma sala", code=code, name=name)

        #GERANDO UMA SALA
        room = code
        if create != False:
            room = generate_uni_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("homepage.html", error="Esta sala não existe", code=code, name=name)
        
        #guardando informações na session, deforma temporária
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("homepage.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

#enviado mensagem a todos na room
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} disse: {data['data']}")


#conectando usuário com socket
@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "entrou na sala"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} entrou na sala {room}")

#desconectando usuário do chat
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms: #se todos deixarem a room, apagar ela
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name": name, "message": "deixou a sala"}, to=room)
    print(f"{name} deixou a sala {room}")


if __name__ == "__main__":
    socketio.run(app, debug=True),

    #56:02 continua