from Bot.Player import Player
JOGADORES = [Player() for _ in range(22)]

def get_jogadores():
    return JOGADORES
def atualizar_lapdata(lap_data_packet):
    for idx,lap in enumerate(lap_data_packet.m_lap_data):
      jogador = JOGADORES[idx]
      jogador.position = lap.m_position
      jogador.currentLapTime = lap.m_current_lap_time/ 1000.0
      jogador.bestLapTime = lap.m_best_lap_time / 1000.0
      jogador.lastLapTime = lap.m_last_lap_time / 1000.0
      try:
          jogador.currentSectors= [
          lap.m_sector1_time_in_ms / 1000.0,
          lap.m_sector2_time_in_ms / 1000.0,
          lap.m_sector3_time_in_ms / 1000.0,
           ]
      except AttributeError:
        jogador.currentSectors = [0.0 , 0.0 ,0.0]
    
      jogador.tyresAgeLaps = lap.m_tyres_age_laps
      jogador.pit = lap.m_pit_status != 0
      jogador.currentLapInvalid = lap.m_invalid_lap == 1

def damage_data(packet):
   for idx,damage in enumerate(packet.m_car_damage_data):
      jogador = JOGADORES[idx]
      jogador.FrontLeftWingDamage = damage.m_front_left_wing_damage
      jogador.FrontRightWingDamage = damage.m_front_right_wing_damage
      jogador.rearWingDamage = damage.m_rear_wing_damage
      jogador.floorDamage = damage.m_floor_damage
      jogador.diffuserDamage = damage.m_diffuser_damage
      jogador.sidepodDamage = damage.m_sidepod_damage

def telemetry_data(packet):
   for idx,telemetry in enumerate(packet.m_car_telematry):
      jogador= JOGADORES[idx]
      jogador.speed = telemetry.m_speed
      jogador.ERS_pourcentage = telemetry.m_ers_store_energy / 400000 * 100  # ERS em %
      jogador.drs = telemetry.m_drs
      jogador.ERS_mode = telemetry.m.ERS
      jogador.speed_trap = telemetry.m_speed_trap
      jogador.fuelMix = telemetry.m_fuelMix
      jogador.aiControlled = telemetry.m_Ai



   
  