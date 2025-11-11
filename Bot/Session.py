from utils.dictionnaries import session_dictionary, conversion, track_dictionary, weather_dictionary, color_flag_dict


class WeatherForecastSample:
    def __init__(self, time, weather, tktp, airtp, rainP):
        self.time = time
        self.weather = weather
        self.trackTemp = tktp
        self.airTemp = airtp
        self.rainPercentage = rainP
        self.weatherForecastAccuracy = -1

    def __repr__(self):
        return f"{self.time}m : {weather_dictionary[self.weather]}, Track : {self.trackTemp}°C, " \
               f"Air : {self.airTemp}°C, Humidity : {self.rainPercentage}% "

    def __str__(self):
        return f"{self.time}m : {weather_dictionary[self.weather]}, Track : {self.trackTemp}°C, " \
               f"Air : {self.airTemp}°C, Humidity : {self.rainPercentage}% "


class Session:
    def __init__(self):
        self.m_track_id = -1
        self.m_track_name = "Desconhecida"
        self.airTemperature = 0
        self.trackTemperature = 0
        self.nbLaps = 0
        self.currentLap = 0
        self.tour_precedent = 0
        self.Seance = 0
        self.Finished = False
        self.time_left = 0
        self.legende = ""
        self.track = -1
        self.marshalZones = []
        self.idxBestLapTime = -1
        self.bestLapTime = 5000
        self.safetyCarStatus = 0
        self.trackLength = 0
        self.weatherList: list[WeatherForecastSample] = []
        self.nb_weatherForecastSamples = 0
        self.weatherForecastAccuracy = 0
        self.startTime = 0
        self.nb_players = 22
        self.formationLapDone = False
        self.circuit_changed = False
        self.segments = []
        self.num_marshal_zones = 0
        self.packet_received = [0]*14
        self.anyYellow = False

    def add_slot(self, slot):
        self.weatherList.append(WeatherForecastSample(slot.m_time_offset, slot.m_weather, slot.m_track_temperature,
                                                      slot.m_air_temperature, slot.m_rain_percentage))

    def clear_slot(self):
        self.weatherList = []

    def title_display(self):
        if self.Seance == 18:
            string = f"Time Trial : {track_dictionary[self.track][0]}"
        elif self.Seance in [15,16,17]:
            string = f"Session : {session_dictionary[self.Seance]}, Lap : {self.currentLap}/{self.nbLaps}, " \
                        f"Air : {self.airTemperature}°C / Track : {self.trackTemperature}°C"
        elif self.Seance in [5,6,7,8,9]:
            string = f" Qualy : {conversion(self.time_left, 1)}"
        else:
            string = f" FP : {conversion(self.time_left, 1)}"
        return string

    def update_marshal_zones(self, map_canvas):
        for i in range(len(self.segments)):
            map_canvas.itemconfig(self.segments[i], fill=color_flag_dict[self.marshalZones[i].m_zone_flag])

SESSION = Session()
class SessionData:
    def __init__(self):
        self.Seance = 0
        self.m_weather = 0
        self.m_air_temperature = 0
        self.m_track_temperature = 0
        self.m_total_laps = 0
        self.bestLapTime = 5000
        self.safetyCarStatus = 0
        self.weatherList: list[WeatherForecastSample] = []
        self.Finished = False
        self.anyYellow = False
        self.rainPercentage = 0

    def atualizar(self, packet):
        self.Seance = packet.m_session_type
        self.m_weather = packet.m_weather
        self.m_air_temperature = packet.m_air_temperature
        self.m_track_temperature = packet.m_track_temperature
        self.m_total_laps = packet.m_total_laps
        self.rainPercentage = getattr(packet, "m_rain_percentage", 0)
        self.track = packet.m_track_id

    def get_track_name(self, track_id):
        tracks = {
            0: "Melbourne",
            1: "Paul Ricard",
            2: "Shanghai",
            3: "Sakhir (Bahrain)",
            4: "Catalunya",
            5: "Monaco",
            6: "Montreal",
            7: "Silverstone",
            8: "Hockenheim",
            9: "Hungaroring",
            10: "Spa",
            11: "Monza",
            12: "Singapore",
            13: "Suzuka",
            14: "Abu Dhabi",
            15: "Texas",
            16: "Brazil",
            17: "Austria",
            18: "Sochi",
            19: "Mexico",
            20: "Baku (Azerbaijan)",
            21: "Sakhir Short",
            22: "Silverstone Short",
            23: "Texas Short",
            24: "Suzuka Short",
            25: "Hanoi",
            26: "Zandvoort",
            27: "Imola",
            28: "Portimão",
            29: "Jeddah",
            30: "Miami",
            31: "Las Vegas",
            32: "Losail (Qatar)",
        }
        return tracks.get(track_id, "Unknown Track")


def atualizar_SessionData(pacote_session):
    from Bot.Session import SESSION
    SESSION.atualizar(pacote_session)
    
    track_id = pacote_session.m_track_id
    nome_pista = SESSION.get_track_name(track_id)
    
    print(f"🏁 Pista: {nome_pista} (ID: {track_id})")
    
    # Salva na sessão
    SESSION.m_track_name = nome_pista


