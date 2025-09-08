import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Calendar, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const HistoricoFinanceiro = () => {
  const [historico, setHistorico] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistorico();
  }, []);

  const fetchHistorico = async () => {
    try {
      const response = await axios.get(`${API}/financeiro/historico`);
      setHistorico(response.data.historico || []);
    } catch (error) {
      console.error('Erro ao carregar histórico:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const getMonthName = (month) => {
    const months = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    return months[month - 1];
  };

  const getTipoBadge = (tipo) => {
    return tipo === 'receita' ? (
      <Badge className="bg-green-100 text-green-800">
        <TrendingUp className="mr-1 h-3 w-3" />
        Receitas
      </Badge>
    ) : (
      <Badge className="bg-red-100 text-red-800">
        <TrendingDown className="mr-1 h-3 w-3" />
        Despesas
      </Badge>
    );
  };

  // Agrupar dados por mês/ano
  const groupedData = historico.reduce((acc, item) => {
    const key = `${item._id.year}-${item._id.month}`;
    if (!acc[key]) {
      acc[key] = {
        year: item._id.year,
        month: item._id.month,
        receitas: 0,
        despesas: 0,
        totalReceitas: 0,
        totalDespesas: 0
      };
    }
    
    if (item._id.tipo === 'receita') {
      acc[key].receitas = item.total;
      acc[key].totalReceitas = item.count;
    } else {
      acc[key].despesas = item.total;
      acc[key].totalDespesas = item.count;
    }
    
    return acc;
  }, {});

  const monthlyData = Object.values(groupedData).sort((a, b) => {
    if (a.year !== b.year) return b.year - a.year;
    return b.month - a.month;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Histórico Financeiro</h1>
        <p className="text-gray-600">Relatório histórico mensal de receitas e despesas</p>
      </div>

      {monthlyData.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-gray-400 mb-4" />
            <p className="text-gray-500 text-center">
              Nenhum dado histórico encontrado.<br />
              Adicione transações financeiras para visualizar o histórico.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {monthlyData.map((data, index) => {
            const saldo = data.receitas - data.despesas;
            const totalTransacoes = data.totalReceitas + data.totalDespesas;
            
            return (
              <Card key={`${data.year}-${data.month}`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-5 w-5 text-blue-600" />
                      <CardTitle>
                        {getMonthName(data.month)} {data.year}
                      </CardTitle>
                    </div>
                    <Badge variant="outline">
                      {totalTransacoes} transação(ões)
                    </Badge>
                  </div>
                  <CardDescription>
                    Resumo financeiro do período
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Receitas */}
                    <div className="bg-green-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-green-700">Receitas</span>
                        <TrendingUp className="h-4 w-4 text-green-600" />
                      </div>
                      <div className="text-2xl font-bold text-green-700">
                        {formatCurrency(data.receitas)}
                      </div>
                      <div className="text-xs text-green-600">
                        {data.totalReceitas} transação(ões)
                      </div>
                    </div>

                    {/* Despesas */}
                    <div className="bg-red-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-red-700">Despesas</span>
                        <TrendingDown className="h-4 w-4 text-red-600" />
                      </div>
                      <div className="text-2xl font-bold text-red-700">
                        {formatCurrency(data.despesas)}
                      </div>
                      <div className="text-xs text-red-600">
                        {data.totalDespesas} transação(ões)
                      </div>
                    </div>

                    {/* Saldo */}
                    <div className={`${saldo >= 0 ? 'bg-blue-50' : 'bg-orange-50'} rounded-lg p-4`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-sm font-medium ${saldo >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                          Saldo
                        </span>
                        <BarChart3 className={`h-4 w-4 ${saldo >= 0 ? 'text-blue-600' : 'text-orange-600'}`} />
                      </div>
                      <div className={`text-2xl font-bold ${saldo >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                        {formatCurrency(saldo)}
                      </div>
                      <div className={`text-xs ${saldo >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                        {saldo >= 0 ? 'Positivo' : 'Negativo'}
                      </div>
                    </div>

                    {/* Variação percentual */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Resultado</span>
                        <div className={`flex items-center ${saldo >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {saldo >= 0 ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                      <div className={`text-lg font-semibold ${saldo >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                        {saldo >= 0 ? 'Lucro' : 'Prejuízo'}
                      </div>
                      <div className="text-xs text-gray-600">
                        {((data.receitas / (data.receitas + data.despesas)) * 100).toFixed(1)}% receitas
                      </div>
                    </div>
                  </div>

                  {/* Barra de progresso */}
                  <div className="mt-4">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Proporção Receitas vs Despesas</span>
                      <span>{totalTransacoes} transações</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-l-full"
                        style={{
                          width: `${(data.receitas / (data.receitas + data.despesas)) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default HistoricoFinanceiro;