# sniffer_simples.py  — rodar com o main.py FECHADO
import socket, struct

UDP_IP, UDP_PORT = "0.0.0.0", 20777

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"🎧 Escutando Participants (packet 4) em {UDP_IP}:{UDP_PORT}")
    print(f"{'CAR':<4} {'DRIVER_ID':<10} {'TEAM_ID':<8} {'NUM':<4} {'NOME'}")
    print("-" * 60)

    vistos = {}
    while True:
        data, _ = sock.recvfrom(4096)
        if len(data) < 7 or data[6] != 4:
            continue

        fmt   = struct.unpack('<H', data[0:2])[0]
        hsize = 29 if fmt >= 2024 else 24
        n     = data[hsize]
        off   = hsize + 1

        for i in range(n):
            if off + 60 > len(data):
                break

            driver_id = data[off + 1]          # <-- ID do piloto
            team_id   = data[off + 3]
            race_num  = data[off + 5]
            nome      = (data[off + 7: off + 7 + 32]
                         .split(b'\x00')[0]
                         .decode('utf-8', errors='ignore')
                         .strip())

            if nome and vistos.get(i) != nome:
                vistos[i] = nome
                print(f"{i:<4} {driver_id:<10} {team_id:<8} {race_num:<4} {nome}")

            off += 60

if __name__ == "__main__":
    main()