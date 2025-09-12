import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Plus, Warehouse, Package, TrendingUp, TrendingDown } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CNPJS_CONFIG = {
  "11111111000101": "EMPRESA ABC",
  "22222222000102": "EMPRESA XYZ", 
  "33333333000103": "EMPRESA 123",
  "44444444000104": "EMPRESA DEF",
  "55555555000105": "EMPRESA GHI"
};

const Estoque = () => {
  const [produtos, setProdutos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAjusteDialogOpen, setIsAjusteDialogOpen] = useState(false);
  const [produtoSelecionado, setProdutoSelecionado] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [ajusteData, setAjusteData] = useState({
    cnpj: '',
    quantidade: 0,
    motivo: ''
  });

  useEffect(() => {
    fetchProdutos();
  }, []);

  const fetchProdutos = async () => {
    try {
      const response = await axios.get(`${API}/produtos`);
      setProdutos(response.data);
    } catch (error) {
      console.error('Erro ao carregar produtos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAjusteEstoque = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/estoque/ajuste`, {
        produto_id: produtoSelecionado.id,
        cnpj: ajusteData.cnpj,
        quantidade: parseInt(ajusteData.quantidade),
        motivo: ajusteData.motivo
      });
      
      fetchProdutos();
      setIsAjusteDialogOpen(false);
      resetAjusteForm();
    } catch (error) {
      console.error('Erro ao ajustar estoque:', error);
      alert('Erro ao ajustar estoque');
    }
  };

  const abrirAjusteEstoque = (produto) => {
    setProdutoSelecionado(produto);
    setIsAjusteDialogOpen(true);
  };

  const resetAjusteForm = () => {
    setAjusteData({
      cnpj: '',
      quantidade: 0,
      motivo: ''
    });
    setProdutoSelecionado(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAjusteData(prev => ({ ...prev, [name]: value }));
  };

  const getEstoqueBadge = (estoque) => {
    if (estoque === 0) {
      return <Badge variant="secondary">Sem estoque</Badge>;
    } else if (estoque < 0) {
      return <Badge variant="destructive">Negativo ({estoque})</Badge>;
    } else if (estoque <= 10) {
      return <Badge variant="secondary">Baixo ({estoque})</Badge>;
    } else {
      return <Badge variant="default">Normal ({estoque})</Badge>;
    }
  };

  const filteredProdutos = produtos.filter(produto =>
    produto.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    produto.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (produto.categoria && produto.categoria.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Calcular estatísticas
  const estatisticas = {
    totalProdutos: produtos.length,
    produtosSemEstoque: produtos.filter(p => p.estoque_total === 0).length,
    produtosEstoqueBaixo: produtos.filter(p => p.estoque_total > 0 && p.estoque_total <= 10).length,
    valorEstoque: produtos.reduce((total, p) => total + (p.estoque_total * p.custo_medio), 0)
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Controle de Estoque</h1>
          <p className="text-gray-600">Gerencie o estoque multi-CNPJ em tempo real</p>
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
            <p className="text-xs text-muted-foreground">produtos cadastrados</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sem Estoque</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{estatisticas.produtosSemEstoque}</div>
            <p className="text-xs text-muted-foreground">produtos zerados</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Estoque Baixo</CardTitle>
            <TrendingUp className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{estatisticas.produtosEstoqueBaixo}</div>
            <p className="text-xs text-muted-foreground">produtos baixos</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <Warehouse className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
              }).format(estatisticas.valorEstoque)}
            </div>
            <p className="text-xs text-muted-foreground">valor do estoque</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Estoque por Produto</CardTitle>
          <CardDescription>
            Estoque detalhado por CNPJ - {filteredProdutos.length} produto(s) {searchTerm && `para "${searchTerm}"`}
          </CardDescription>
          <div className="flex items-center space-x-2">
            <Input
              placeholder="Buscar por nome, SKU ou categoria..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
          </div>
        </CardHeader>
        <CardContent>
          {filteredProdutos.length === 0 ? (
            <div className="text-center py-8">
              <Warehouse className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">
                {searchTerm ? 'Nenhum produto encontrado para a busca' : 'Nenhum produto no estoque'}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Produto</TableHead>
                    <TableHead>SKU</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Estoques por CNPJ</TableHead>
                    <TableHead>Valor Total</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredProdutos.map((produto) => (
                    <TableRow key={produto.id}>
                      <TableCell>
                        <div className="font-medium">{produto.nome}</div>
                        <div className="text-sm text-gray-500">{produto.marca}</div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{produto.sku}</TableCell>
                      <TableCell>{produto.categoria}</TableCell>
                      <TableCell className="font-bold text-lg">
                        {produto.estoque_total}
                      </TableCell>
                      <TableCell>
                        {getEstoqueBadge(produto.estoque_total)}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {produto.estoques_cnpj?.map((estoque) => (
                            <div key={estoque.cnpj} className="flex justify-between text-xs border rounded px-2 py-1">
                              <span className="font-medium">{CNPJS_CONFIG[estoque.cnpj]}:</span>
                              <span className={`font-bold ${
                                estoque.quantidade < 0 ? 'text-red-600' : 
                                estoque.quantidade === 0 ? 'text-gray-500' : 
                                'text-green-600'
                              }`}>
                                {estoque.quantidade}
                              </span>
                            </div>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium text-green-600">
                        {new Intl.NumberFormat('pt-BR', {
                          style: 'currency',
                          currency: 'BRL'
                        }).format(produto.estoque_total * produto.custo_medio)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => abrirAjusteEstoque(produto)}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Ajustar
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog de Ajuste de Estoque */}
      <Dialog open={isAjusteDialogOpen} onOpenChange={setIsAjusteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajustar Estoque</DialogTitle>
            <DialogDescription>
              Produto: {produtoSelecionado?.nome} (SKU: {produtoSelecionado?.sku})
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAjusteEstoque} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cnpj">CNPJ *</Label>
              <Select onValueChange={(value) => setAjusteData(prev => ({...prev, cnpj: value}))}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o CNPJ" />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CNPJS_CONFIG).map(([cnpj, nome]) => (
                    <SelectItem key={cnpj} value={cnpj}>
                      {nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="quantidade">Quantidade *</Label>
              <Input
                id="quantidade"
                name="quantidade"
                type="number"
                value={ajusteData.quantidade}
                onChange={handleInputChange}
                placeholder="Digite a quantidade (positivo = entrada, negativo = saída)"
                required
              />
              <p className="text-xs text-gray-500">
                Positivo para entrada, negativo para saída
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="motivo">Motivo *</Label>
              <Input
                id="motivo"
                name="motivo"
                value={ajusteData.motivo}
                onChange={handleInputChange}
                placeholder="Ex: Inventário, Perda, Correção"
                required
              />
            </div>
            
            <div className="flex justify-end space-x-2">
              <Button 
                type="button" 
                variant="outline" 
                onClick={() => {
                  setIsAjusteDialogOpen(false);
                  resetAjusteForm();
                }}
              >
                Cancelar
              </Button>
              <Button type="submit">
                Confirmar Ajuste
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Estoque;