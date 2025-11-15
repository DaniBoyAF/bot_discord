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
        self.m_weather = 0
        self.m_track_temperature = 0
        self.m_air_temperature = 0
        self.m_total_laps = 0
        self.m_track_length = 0
        self.m_session_type = 0
        self.m_track_id = -1
        self.m_track_name = "Desconhecida"
        self.m_formula = 0
        self.m_session_time_left = 0
        self.m_session_duration = 0
        self.m_pit_speed_limit = 0
        self.m_game_paused = 0
        self.m_is_spectating = 0
        self.m_spectator_car_index = 0
        self.m_sli_pro_native_support = 0
        self.m_num_marshal_zones = 0
        self.m_marshal_zones = []
        self.m_safety_car_status = 0
        self.m_network_game = 0
        self.m_num_weather_forecast_samples = 0
        self.m_forecast_accuracy = 0
        self.m_ai_difficulty = 0
        self.m_season_link_identifier = 0
        self.m_weekend_link_identifier = 0
        self.m_session_link_identifier = 0
        self.m_pit_stop_window_ideal_lap = 0
        self.m_pit_stop_window_latest_lap = 0
        self.m_pit_stop_rejoin_position = 0
        self.m_steering_assist = 0
        self.m_braking_assist = 0
        self.m_gearbox_assist = 0
        self.m_pit_assist = 0
        self.m_pit_release_assist = 0
        self.m_ersassist = 0
        self.m_drsassist = 0
        self.m_dynamic_racing_line = 0
        self.m_dynamic_racing_line_type = 0
        self.m_game_mode = 0
        self.m_rule_set = 0
        self.m_time_of_day = 0
        self.m_session_length = 0
        self.m_speed_units_lead_player = 0
        self.m_temperature_units_lead_player = 0
        self.m_speed_units_secondary_player = 0
        self.m_temperature_units_secondary_player = 0
        self.m_num_safety_car_periods = 0
        self.m_num_virtual_safety_car_periods = 0
        self.m_num_red_flag_periods = 0

        # Atributos extras
        self.flag = "Verde"
        self.SafetyCarStatus = "Nenhum"
        self.rainPercentage = 0
        self.Seance = "Desconhecida"
        self.weather = "Limpo"
        self.track_name = "Desconhecida"
        self.currentLap = 0

    def get_track_name(self, track_id):
        """Retorna o nome da pista baseado no ID"""
        tracks = {
            0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai",
            3: "Sakhir (Bahrain)", 4: "Catalunya", 5: "Monaco",
            6: "Montreal", 7: "Silverstone", 8: "Hockenheim",
            9: "Hungaroring", 10: "Spa", 11: "Monza",
            12: "Singapore", 13: "Suzuka", 14: "Abu Dhabi",
            15: "Texas", 16: "Brazil", 17: "Austria",
            18: "Sochi", 19: "Mexico", 20: "Baku (Azerbaijan)",
            21: "Sakhir Short", 22: "Silverstone Short",
            23: "Texas Short", 24: "Suzuka Short", 25: "Hanoi",
            26: "Zandvoort", 27: "Imola", 28: "Portimão",
            29: "Jeddah", 30: "Miami", 31: "Las Vegas",
            32: "Losail (Qatar)"
        }
        return tracks.get(track_id, "Unknown Track")

    def atualizar(self, pacote_session):
        """Atualiza os dados da sessão com base no pacote recebido"""
        for attr in dir(pacote_session):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(pacote_session, attr))

        self.m_track_name = self.get_track_name(self.m_track_id)
        self.track_name = self.m_track_name
        self.rainPercentage = getattr(pacote_session, "m_rain_percentage",)
        if getattr(self, "m_num_marshal_zones", 0) > 0:
            mz = getattr(self, "m_marshal_zones", [])
            if mz:
                flag_id = mz[0].m_zone_flag
                self.flag = color_flag_dict.get(flag_id, "Verde")
        self.weather = weather_dictionary.get(self.m_weather, "Desconhecido")
        self.weather = weather_dictionary.get(self.m_weather, "Desconhecido")


# Instância global
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
    SESSION.atualizar(pacote_session)
    print(f"🏁 Pista: {SESSION.track_name} (ID: {pacote_session.m_track_id})")


