import React, { useState, useEffect } from 'react';
import { Trophy, Zap, Flag, Clock } from 'lucide-react';

const GPDashboard = () => {
  const [easterEggActive, setEasterEggActive] = useState(false);
  const [keySequence, setKeySequence] = useState([]);
  const [showSecret, setShowSecret] = useState(false);
  const [raceData, setRaceData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight'];

  // Carregar JSON automaticamente
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
      // Não mostrar alert, apenas logar o erro
    } finally {
      setIsLoading(false);
    }
  };

  // Processar dados dos pilotos
  const processRacerData = (racer) => {
    const validLaps = racer.voltas.filter(lap => {
      if (!lap.setores || lap.setores.length !== 3) return false;
      const allSectorsValid = lap.setores.every(setor => setor >= 15);
      if (!allSectorsValid) return false;
      const sectorsSum = lap.setores.reduce((a, b) => a + b, 0);
      const diff = Math.abs(sectorsSum - lap.tempo_total);
      return diff < 0.1;
    });

    if (validLaps.length === 0) return null;

    const lapTimes = validLaps.map(lap => lap.tempo_total);
    const avgTime = lapTimes.reduce((a, b) => a + b, 0) / lapTimes.length;
    const bestLap = Math.min(...lapTimes);

    return {
      nome: racer.nome,
      numero: racer.numero,
      position: racer.position,
      tyres: racer.tyres,
      bestLap: bestLap,
      avgTime: avgTime,
      color: `#${Math.floor(Math.random()*16777215).toString(16).padStart(6, '0')}`
    };
  };

  const racers = raceData
    .map(processRacerData)
    .filter(r => r !== null);

  const calculateWeightedAvg = (racer) => {
    return (racer.avgTime * 0.7 + racer.bestLap * 0.3).toFixed(3);
  };

  const sortedRacers = [...racers].sort((a, b) => 
    parseFloat(calculateWeightedAvg(a)) - parseFloat(calculateWeightedAvg(b))
  );

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${mins}:${secs.padStart(6, '0')}`;
  };

  useEffect(() => {
    const handleKeyPress = (e) => {
      const newSequence = [...keySequence, e.key].slice(-8);
      setKeySequence(newSequence);
      
      if (JSON.stringify(newSequence) === JSON.stringify(konamiCode)) {
        setEasterEggActive(true);
        setShowSecret(true);
        setTimeout(() => setShowSecret(false), 5000);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [keySequence]);

  // Tela de loading ou sem dados
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-6xl mb-4 animate-bounce">🏎️</div>
          <h2 className="text-3xl font-bold">Carregando dados...</h2>
        </div>
      </div>
    );
  }

  if (sortedRacers.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 flex items-center justify-center">
        <div className="text-center text-white">
          <Flag className="mx-auto mb-4" size={64} />
          <h2 className="text-3xl font-bold mb-4">Aguardando dados da corrida</h2>
          <p className="text-xl text-gray-400">Coloque o arquivo dados_de_voltas.json na pasta public/</p>
        </div>
      </div>
    );
  }

  const maxWeighted = Math.max(...sortedRacers.map(r => parseFloat(calculateWeightedAvg(r))));

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 p-8 relative overflow-hidden">
      {/* Background racing pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.05) 10px, rgba(255,255,255,.05) 20px)'
        }}/>
      </div>

      {/* Easter Egg Secret Message */}
      {showSecret && (
        <div className="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-80 animate-pulse">
          <div className="bg-gradient-to-r from-yellow-400 via-red-500 to-pink-500 p-8 rounded-lg text-center transform rotate-3 animate-bounce">
            <h1 className="text-6xl font-bold text-white mb-4">🏎️ BOX BOX BOX! 🏎️</h1>
            <p className="text-3xl text-white mb-2">CÓDIGO KONAMI ATIVADO!</p>
            <p className="text-xl text-white">Você achou o Easter Egg! 🎉</p>
            <p className="text-lg text-white mt-4">S🅱️innala! 🌀</p>
          </div>
        </div>
      )}

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-6xl font-bold text-white mb-4 flex items-center justify-center gap-4">
            <Flag className="text-red-500" size={48} />
            Mexico GP 2025 🇲🇽
            <Flag className="text-green-500" size={48} />
          </h1>
          <p className="text-2xl text-gray-300">Race Pace (Média Ponderada: 70% avg + 30% best)</p>
          <p className="text-sm text-gray-400 mt-2">💡 Dica: Tente o código Konami... ↑↑↓↓←→←→</p>
        </div>

        {/* Podium */}
        <div className="grid grid-cols-3 gap-4 mb-12 max-w-4xl mx-auto">
          {[1, 0, 2].map((sortIdx) => {
            if (!sortedRacers[sortIdx]) return null;
            const racer = sortedRacers[sortIdx];
            const actualPosition = sortIdx;
            const heights = ['h-56', 'h-48', 'h-40'];
            const colors = [
              'from-yellow-600 to-yellow-400',
              'from-gray-600 to-gray-400', 
              'from-orange-600 to-orange-400'
            ];
            
            return (
              <div key={racer.nome} className="text-center">
                <div className={`${heights[actualPosition]} bg-gradient-to-t ${colors[actualPosition]} rounded-t-lg flex items-center justify-center flex-col shadow-2xl transform hover:scale-105 transition-transform`}>
                  <Trophy size={48} className="text-white mb-2" />
                  <span className="text-4xl font-bold text-white">P{actualPosition + 1}</span>
                  <span className="text-xl font-semibold text-white mt-2">{racer.nome}</span>
                  <span className="text-lg text-white">{formatTime(parseFloat(calculateWeightedAvg(racer)))}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Race Pace Chart */}
        <div className="bg-gray-800 bg-opacity-90 rounded-lg p-8 shadow-2xl backdrop-blur-sm">
          <h2 className="text-3xl font-bold text-white mb-6 flex items-center gap-2">
            <Zap className="text-yellow-400" />
            Ritmo de Corrida
          </h2>
          
          <div className="space-y-3">
            {sortedRacers.map((racer, idx) => {
              const weighted = parseFloat(calculateWeightedAvg(racer));
              const leaderTime = parseFloat(calculateWeightedAvg(sortedRacers[0]));
              const diff = weighted - leaderTime;
              const barWidth = (weighted / maxWeighted) * 100;
              
              return (
                <div key={racer.nome} className="group">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-lg font-bold text-white w-8">{idx + 1}.</span>
                    <span className="text-lg text-white font-semibold flex-1">{racer.nome}</span>
                    <span className="text-sm text-gray-400">#{racer.numero}</span>
                    <span className="text-sm px-2 py-1 bg-gray-700 rounded text-white">{racer.tyres}</span>
                  </div>
                  
                  <div className="flex items-center gap-3 ml-11">
                    <div className="flex-1 bg-gray-700 rounded-full h-8 relative overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all duration-1000 flex items-center justify-end pr-3 group-hover:brightness-125"
                        style={{
                          width: `${barWidth}%`,
                          background: `linear-gradient(to right, ${racer.color}, ${racer.color}dd)`
                        }}
                      >
                        <span className="text-white font-bold text-sm">{formatTime(weighted)}</span>
                      </div>
                    </div>
                    <div className="flex gap-3 text-sm min-w-[180px]">
                      <span className={`font-semibold w-16 ${idx === 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                        {idx === 0 ? '—' : `+${diff.toFixed(3)}`}
                      </span>
                      <div className="flex items-center gap-1 text-gray-400 text-xs">
                        <Clock size={12} />
                        <span>Best: {formatTime(racer.bestLap)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Stats Footer */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-gray-800 bg-opacity-90 p-4 rounded-lg">
            <p className="text-gray-400 text-sm">Mais Rápido</p>
            <p className="text-2xl font-bold text-green-400">{sortedRacers[0].nome}</p>
          </div>
          <div className="bg-gray-800 bg-opacity-90 p-4 rounded-lg">
            <p className="text-gray-400 text-sm">Total de Pilotos</p>
            <p className="text-2xl font-bold text-blue-400">{racers.length}</p>
          </div>
          <div className="bg-gray-800 bg-opacity-90 p-4 rounded-lg">
            <p className="text-gray-400 text-sm">Melhor Volta Geral</p>
            <p className="text-2xl font-bold text-yellow-400">{formatTime(Math.min(...racers.map(r => r.bestLap)))}</p>
          </div>
        </div>

        {easterEggActive && (
          <div className="mt-8 text-center">
            <p className="text-green-400 text-xl animate-pulse">
              🏆 Achievement Unlocked: Racing Fan Supreme! 🏆
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GPDashboard;