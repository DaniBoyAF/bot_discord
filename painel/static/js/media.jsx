import React, { useState, useEffect } from 'react';
import { Upload, Flag } from 'lucide-react';

const GPLaptimeAnalysis = () => {
  const [raceData, setRaceData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [trafficFilter, setTrafficFilter] = useState('all');
  const [sortBy, setSortBy] = useState('mean');

  // Carrega JSON automaticamente quando o componente monta
  useEffect(() => {
    loadJsonFromUrl('/dados_de_voltas.json');
  }, []);

  // Função para carregar JSON de uma URL
  const loadJsonFromUrl = async (url) => {
    setIsLoading(true);
    try {
      const response = await fetch(url);
      const data = await response.json();
      setRaceData(Array.isArray(data) ? data : [data]);
    } catch (error) {
      console.error('Erro ao carregar JSON da URL:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Upload manual de arquivo
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsLoading(true);
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      setRaceData(Array.isArray(data) ? data : [data]);
    } catch (error) {
      alert('Erro ao ler o arquivo JSON. Verifique o formato!');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Função auxiliar para detectar safety car (períodos com 2+ voltas consecutivas lentas)
  const countConsecutiveSafetyCarLaps = (validLaps, meanTime) => {
    let consecutiveCount = 0;
    let totalSafetyLaps = 0;
    
    validLaps.forEach(lap => {
      if (lap.tempo_total > meanTime + 15) {
        consecutiveCount++;
      } else {
        // Se tinha 2+ voltas consecutivas, conta como safety car
        if (consecutiveCount > 1) {
          totalSafetyLaps += consecutiveCount;
        }
        consecutiveCount = 0;
      }
    });
    
    // Verifica o último período
    if (consecutiveCount > 1) {
      totalSafetyLaps += consecutiveCount;
    }
    
    return totalSafetyLaps;
  };

  const processDriverData = (driver) => {
    if (!driver || !driver.voltas) return null;

    // Filtrar voltas válidas
    const validLaps = driver.voltas.filter(lap => {
      if (!lap.setores || lap.setores.length !== 3) return false;
      
      const allSectorsValid = lap.setores.every(setor => setor >= 15);
      if (!allSectorsValid) return false;
      
      const sectorsSum = lap.setores.reduce((a, b) => a + b, 0);
      const diff = Math.abs(sectorsSum - lap.tempo_total);
      return diff < 0.1;
    });

    if (validLaps.length === 0) return null;

    const lapTimes = validLaps.map(lap => lap.tempo_total);
    const meanTime = lapTimes.reduce((a, b) => a + b, 0) / lapTimes.length;
    const bestLap = Math.min(...lapTimes);

    // Identificar pit stops (voltas isoladas muito lentas > média + 22s)
    const pitStops = validLaps.filter((lap, idx) => {
      const isSlow = lap.tempo_total > meanTime + 22;
      const prevSlow = idx > 0 && validLaps[idx - 1].tempo_total > meanTime + 15;
      const nextSlow = idx < validLaps.length - 1 && validLaps[idx + 1].tempo_total > meanTime + 15;
      
      // É pit stop se for lenta mas não tem voltas lentas adjacentes
      return isSlow && !prevSlow && !nextSlow;
    }).length;

    // Identificar safety car (apenas períodos com 2+ voltas consecutivas lentas)
    const safetyCarLaps = countConsecutiveSafetyCarLaps(validLaps, meanTime);

    return {
      nome: driver.nome,
      numero: driver.numero,
      tyres: driver.tyres,
      position: driver.position,
      lapTimes: lapTimes,
      validLaps: validLaps,
      meanTime: meanTime,
      bestLap: bestLap,
      pitStops: pitStops,
      safetyCarLaps: safetyCarLaps,
      totalLaps: driver.voltas.length,
      validLapsCount: validLaps.length
    };
  };

  const processedDrivers = raceData
    .map(processDriverData)
    .filter(d => d !== null && d.validLapsCount >= 5) // Apenas pilotos com 5+ voltas válidas
    .sort((a, b) => {
      switch(sortBy) {
        case 'best':
          return a.bestLap - b.bestLap;
        case 'name':
          return a.nome.localeCompare(b.nome);
        case 'position':
          return a.position - b.position;
        case 'mean':
        default:
          return a.meanTime - b.meanTime;
      }
    });

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${mins}:${secs.padStart(6, '0')}`;
  };

  const getDriverInitials = (name) => {
    const parts = name.split(' ').filter(p => p.length > 0);
    if (parts.length >= 2) {
      return parts.slice(-2).map(p => p.substring(0, 3).toUpperCase()).join('');
    }
    return name.substring(0, 6).toUpperCase();
  };

  const colors = [
    '#FF6B35', '#004E89', '#1A936F', '#C1666B', '#48A9A6',
    '#E63946', '#457B9D', '#2A9D8F', '#E76F51', '#264653',
    '#F4A261', '#8338EC', '#3A86FF', '#FB5607', '#FFBE0B'
  ];

  if (processedDrivers.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center p-8">
        <div className="bg-white rounded-lg p-12 max-w-2xl text-center shadow-2xl">
          <Flag className="text-red-500 mx-auto mb-6" size={64} />
          <h1 className="text-5xl font-bold text-gray-800 mb-6">Mexico GP 2025 🇲🇽</h1>
          <p className="text-xl text-gray-600 mb-8">Análise de Tempos por Volta</p>
          
          <label className="cursor-pointer">
            <div className="bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold py-4 px-8 rounded-lg inline-flex items-center gap-3 transition-all transform hover:scale-105">
              <Upload size={24} />
              {isLoading ? 'Carregando...' : 'Selecionar Arquivo JSON'}
            </div>
            <input 
              type="file" 
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
          </label>
        </div>
      </div>
    );
  }

  const allLapTimes = processedDrivers.flatMap(d => d.lapTimes);
  const minTime = Math.min(...allLapTimes);
  const maxTime = Math.max(...allLapTimes);
  const yMin = Math.floor((minTime - 2) / 5) * 5;
  const yMax = Math.ceil((maxTime + 2) / 5) * 5;
  const chartHeight = 500;

  const getYPosition = (time) => {
    return chartHeight - ((time - yMin) / (yMax - yMin)) * chartHeight;
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-[1600px] mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 mb-2">
                Mexico GP 2025 🇲🇽
              </h1>
              <p className="text-gray-600">
                Race pace ordered by {
                  sortBy === 'mean' ? 'mean lap time' :
                  sortBy === 'best' ? 'best lap time' :
                  sortBy === 'position' ? 'final position' :
                  'driver name'
                } - All drivers
              </p>
            </div>
            <div className="flex gap-4 items-center flex-wrap">
              {/* Ordenação */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-4 py-2 rounded-lg border-2 border-gray-300 font-semibold bg-white"
              >
                <option value="mean">Ordenar por: Média</option>
                <option value="best">Ordenar por: Melhor Volta</option>
                <option value="position">Ordenar por: Posição Final</option>
                <option value="name">Ordenar por: Nome</option>
              </select>

              {/* Filtros de tráfego */}
              <div className="flex gap-2">
                <button
                  onClick={() => setTrafficFilter('traffic')}
                  className={`px-4 py-2 rounded-lg font-semibold ${trafficFilter === 'traffic' ? 'bg-red-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  ◆ In traffic
                </button>
                <button
                  onClick={() => setTrafficFilter('clean')}
                  className={`px-4 py-2 rounded-lg font-semibold ${trafficFilter === 'clean' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                >
                  ◇ Minimal or no traffic
                </button>
              </div>

              {/* Upload */}
              <label className="cursor-pointer">
                <div className="bg-gray-700 hover:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg inline-flex items-center gap-2">
                  <Upload size={16} />
                  Novo JSON
                </div>
                <input 
                  type="file" 
                  accept=".json"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="relative" style={{ height: chartHeight + 100 }}>
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-20 w-24 flex flex-col justify-between text-sm text-gray-600">
              {Array.from({ length: 6 }, (_, i) => {
                const time = yMax - (i * (yMax - yMin) / 5);
                return (
                  <div key={i} className="text-right pr-2">{formatTime(time)}</div>
                );
              })}
            </div>

            {/* Grid lines */}
            <div className="absolute left-24 right-0 top-0 bottom-20">
              {Array.from({ length: 6 }, (_, i) => (
                <div
                  key={i}
                  className="absolute w-full border-t border-gray-200"
                  style={{ top: `${(i / 5) * 100}%` }}
                />
              ))}

              {/* Driver columns */}
              <div className="flex h-full">
                {processedDrivers.map((driver, driverIdx) => {
                  const color = colors[driverIdx % colors.length];
                  const columnWidth = 100 / processedDrivers.length;

                  return (
                    <div
                      key={driver.nome}
                      className="relative"
                      style={{ width: `${columnWidth}%` }}
                    >
                      {/* Background bar */}
                      <div
                        className="absolute top-0 bottom-0 left-[10%] right-[10%] opacity-20"
                        style={{ 
                          backgroundColor: color,
                          top: `${getYPosition(driver.meanTime + 3)}px`,
                          bottom: `${chartHeight - getYPosition(driver.meanTime - 3)}px`
                        }}
                      />

                      {/* Mean line */}
                      <div
                        className="absolute left-0 right-0 h-0.5"
                        style={{ 
                          backgroundColor: color,
                          top: `${getYPosition(driver.meanTime)}px`
                        }}
                      />

                      {/* Lap time dots */}
                      {driver.lapTimes.map((lapTime, lapIdx) => {
                        const isOutlier = Math.abs(lapTime - driver.meanTime) > 10;
                        return (
                          <div
                            key={lapIdx}
                            className="absolute rounded-full transition-all hover:scale-150"
                            style={{
                              backgroundColor: color,
                              width: isOutlier ? '3px' : '6px',
                              height: isOutlier ? '3px' : '6px',
                              left: `${30 + (lapIdx * (40 / driver.lapTimes.length))}%`,
                              top: `${getYPosition(lapTime) - 3}px`,
                              opacity: isOutlier ? 0.3 : 0.7
                            }}
                            title={`Volta ${lapIdx + 1}: ${formatTime(lapTime)}`}
                          />
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Driver labels at bottom */}
            <div className="absolute left-24 right-0 bottom-0 h-20 flex border-t-2 border-gray-300">
              {processedDrivers.map((driver, idx) => {
                const color = colors[idx % colors.length];
                const columnWidth = 100 / processedDrivers.length;

                return (
                  <div
                    key={driver.nome}
                    className="flex flex-col items-center justify-center text-center px-1"
                    style={{ width: `${columnWidth}%` }}
                  >
                    <div
                      className="w-3 h-3 rounded-full mb-1"
                      style={{ backgroundColor: color }}
                    />
                    <div className="text-xs font-bold" style={{ color: color }}>
                      {getDriverInitials(driver.nome)}
                    </div>
                    <div className="text-xs text-gray-600 font-bold mt-1">
                      {formatTime(driver.meanTime)}
                    </div>
                    <div className="text-[10px] text-gray-500">
                      {driver.pitStops} stop{driver.pitStops !== 1 ? 's' : ''}
                      {driver.safetyCarLaps > 0 && ` | 🚩 ${driver.safetyCarLaps} SC`}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-6 bg-white rounded-lg shadow-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {processedDrivers.map((driver, idx) => (
              <div key={driver.nome} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: colors[idx % colors.length] }}
                />
                <span className="font-semibold">{getDriverInitials(driver.nome)}</span>
                <span className="text-gray-600">- {driver.nome}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GPLaptimeAnalysis;