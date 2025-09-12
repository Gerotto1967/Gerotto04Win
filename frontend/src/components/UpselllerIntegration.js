import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Zap, Package, DollarSign, TrendingUp, Download, Upload, RefreshCw } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UpselllerIntegration = () => {
  const [estoqueUpseller, setEstoqueUpseller] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ultimaAtualizacao, setUltimaAtualizacao] = useState(null);
  const [estatisticas, setEstatisticas] = useState({
    totalProdutos: 0,
    produtosComEstoque: 0,
    valorTotalEstoque: 0
  });

  useEffect(() => {
    fetchEstoqueUpseller();
  }, []);

  const fetchEstoqueUpseller = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/upseller/estoque`);
      setEstoqueUpseller(response.data.produtos);
      setUltimaAtualizacao(new Date());
      
      // Calcular estatísticas
      const stats = response.data.produtos.reduce(
        (acc, produto) => {
          acc.totalProdutos++;
          if (produto.estoque_disponivel > 0) {
            acc.produtosComEstoque++;
          }
          acc.valorTotalEstoque += produto.estoque_disponivel * produto.custo_medio;
          return acc;
        },
        { totalProdutos: 0, produtosComEstoque: 0, valorTotalEstoque: 0 }
      );
      
      setEstatisticas(stats);
      
    } catch (error) {
      console.error('Erro ao buscar estoque:', error);
      alert('Erro ao carregar dados do estoque para Upseller');
    } finally {
      setLoading(false);
    }
  };

  const handleExportarEstoque = () => {
    const dataStr = JSON.stringify(estoqueUpseller, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `estoque-upseller-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const simularVenda = async () => {
    // Simular uma venda para demonstração
    const vendaSimulada = {
      cnpj_vendedor: "11111111000101",
      produtos: [
        {
          sku: estoqueUpseller[0]?.sku || "TESTE001",
          quantidade: 1,
          preco_unitario: estoqueUpseller[0]?.preco_venda || 50.00
        }
      ],
      valor_bruto: estoqueUpseller[0]?.preco_venda || 50.00,
      valor_liquido: (estoqueUpseller[0]?.preco_venda || 50.00) * 0.85, // 15% de taxa
      taxas: (estoqueUpseller[0]?.preco_venda || 50.00) * 0.15,
      pedido_id: "TESTE" + Date.now()
    };

    try {
      const response = await axios.post(`${API}/upseller/venda`, vendaSimulada);
      alert(`Venda simulada processada! Lucro: R$ ${response.data.lucro_bruto.toFixed(2)}`);
      fetchEstoqueUpseller(); // Atualizar dados
    } catch (error) {
      console.error('Erro ao simular venda:', error);
      alert('Erro ao processar venda simulada');
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDateTime = (date) => {
    return date ? date.toLocaleString('pt-BR') : 'Nunca';
  };

  const getEstoqueBadge = (estoque) => {
    if (estoque === 0) {
      return <Badge variant="destructive">Sem Estoque</Badge>;
    } else if (estoque <= 5) {
      return <Badge variant="secondary">Baixo ({estoque})</Badge>;
    } else if (estoque <= 20) {
      return <Badge variant="outline">Normal ({estoque})</Badge>;
    } else {
      return <Badge variant="default">Alto ({estoque})</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Integração Upseller</h1>
          <p className="text-gray-600">Sincronização de estoque e processamento de vendas</p>
        </div>
        
        <div className="flex space-x-2">
          <Button 
            onClick={fetchEstoqueUpseller} 
            disabled={loading}
            variant="outline"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          
          <Button onClick={handleExportarEstoque} variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Exportar JSON
          </Button>
          
          <Button onClick={simularVenda} className="bg-purple-600 hover:bg-purple-700">
            <Zap className="mr-2 h-4 w-4" />
            Simular Venda
          </Button>
        </div>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total de Produtos</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{estatisticas.totalProdutos}</div>
            <p className="text-xs text-muted-foreground">produtos no catálogo</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Com Estoque</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{estatisticas.produtosComEstoque}</div>
            <p className="text-xs text-muted-foreground">produtos disponíveis</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <DollarSign className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(estatisticas.valorTotalEstoque)}
            </div>
            <p className="text-xs text-muted-foreground">valor do estoque</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Última Atualização</CardTitle>
            <RefreshCw className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold text-purple-600">
              {formatDateTime(ultimaAtualizacao)}
            </div>
            <p className="text-xs text-muted-foreground">sincronização</p>
          </CardContent>
        </Card>
      </div>

      {/* Informações da Integração */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="mr-2 h-5 w-5 text-green-600" />
              Envio para Upseller
            </CardTitle>
            <CardDescription>
              Dados enviados automaticamente para o Upseller
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span>✅ Estoque Consolidado:</span>
              <span className="font-medium">Soma de todos os CNPJs</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Custo Médio:</span>
              <span className="font-medium">Calculado automaticamente</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Preço de Venda:</span>
              <span className="font-medium">Configurado por produto</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Disponibilidade:</span>
              <span className="font-medium">Tempo real</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="mr-2 h-5 w-5 text-blue-600" />
              Recebimento do Upseller
            </CardTitle>
            <CardDescription>
              Processamento automático de vendas
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span>✅ Baixa de Estoque:</span>
              <span className="font-medium">Por CNPJ vendedor</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Cálculo de Lucro:</span>
              <span className="font-medium">Preço - Custo Médio</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Conta a Receber:</span>
              <span className="font-medium">Valor líquido</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>✅ Registro de Taxas:</span>
              <span className="font-medium">Como despesa</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabela de Produtos */}
      <Card>
        <CardHeader>
          <CardTitle>Estoque Disponível no Upseller</CardTitle>
          <CardDescription>
            Produtos e quantidades disponíveis para venda no marketplace
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : estoqueUpseller.length === 0 ? (
            <div className="text-center py-8">
              <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">Nenhum produto disponível no estoque</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>SKU</TableHead>
                    <TableHead>Nome do Produto</TableHead>
                    <TableHead>Estoque</TableHead>
                    <TableHead>Custo Médio</TableHead>
                    <TableHead>Preço Venda</TableHead>
                    <TableHead>Margem</TableHead>
                    <TableHead>Valor Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {estoqueUpseller.map((produto) => {
                    const margem = produto.custo_medio > 0 
                      ? ((produto.preco_venda - produto.custo_medio) / produto.custo_medio) * 100 
                      : 0;
                    
                    return (
                      <TableRow key={produto.sku}>
                        <TableCell className="font-mono text-sm">{produto.sku}</TableCell>
                        <TableCell>
                          <div className="font-medium">{produto.nome}</div>
                        </TableCell>
                        <TableCell>
                          {getEstoqueBadge(produto.estoque_disponivel)}
                        </TableCell>
                        <TableCell>{formatCurrency(produto.custo_medio)}</TableCell>
                        <TableCell className="font-medium text-green-600">
                          {formatCurrency(produto.preco_venda)}
                        </TableCell>
                        <TableCell>
                          <span className={`font-medium ${margem >= 30 ? 'text-green-600' : margem >= 15 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {margem.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell className="font-bold">
                          {formatCurrency(produto.estoque_disponivel * produto.custo_medio)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Instruções de Integração */}
      <Card>
        <CardHeader>
          <CardTitle>Como Funciona a Integração</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-3 text-green-600">📤 Envio de Dados (ERP → Upseller)</h4>
              <ol className="text-sm space-y-2 list-decimal list-inside">
                <li>ERP consolida estoque de todos os CNPJs</li>
                <li>Calcula custo médio atualizado</li>
                <li>Envia via API: SKU, Nome, Estoque, Custo, Preço</li>
                <li>Upseller recebe e atualiza catálogo</li>
              </ol>
            </div>
            
            <div>
              <h4 className="font-semibold mb-3 text-blue-600">📥 Recebimento de Vendas (Upseller → ERP)</h4>
              <ol className="text-sm space-y-2 list-decimal list-inside">
                <li>Upseller processa venda e envia dados</li>
                <li>ERP identifica CNPJ que vendeu</li>
                <li>Baixa estoque do CNPJ específico</li>
                <li>Cria conta a receber e registra lucro</li>
              </ol>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default UpselllerIntegration;