import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Plus, Edit, Trash2, Package, Eye, Image } from 'lucide-react';
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

const Produtos = () => {
  const [produtos, setProdutos] = useState([]);
  const [fornecedores, setFornecedores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProduto, setEditingProduto] = useState(null);
  const [viewingMovimentacoes, setViewingMovimentacoes] = useState(null);
  const [movimentacaoDialogOpen, setMovimentacaoDialogOpen] = useState(false);
  const [movimentacoes, setMovimentacoes] = useState([]);
  const [resumoMovimentacoes, setResumoMovimentacoes] = useState({});
  const [formData, setFormData] = useState({
    sku: '',
    ean: '',
    nome: '',
    descricao: '',
    categoria: '',
    marca: '',
    unidade: 'UN',
    valor_compra: 0,
    preco_venda: 0,
    fornecedor_id: '',
    fora_estado: false
  });

  useEffect(() => {
    fetchProdutos();
    fetchFornecedores();
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

  const fetchFornecedores = async () => {
    try {
      const response = await axios.get(`${API}/fornecedores`);
      setFornecedores(response.data);
    } catch (error) {
      console.error('Erro ao carregar fornecedores:', error);
    }
  };

  const fetchMovimentacoes = async (produtoId) => {
    try {
      const response = await axios.get(`${API}/produtos/${produtoId}/movimentacoes`);
      setMovimentacoes(response.data.movimentacoes);
      setResumoMovimentacoes(response.data.resumo);
    } catch (error) {
      console.error('Erro ao carregar movimentações:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        valor_compra: parseFloat(formData.valor_compra),
        preco_venda: parseFloat(formData.preco_venda)
      };

      if (editingProduto) {
        await axios.put(`${API}/produtos/${editingProduto.id}`, data);
      } else {
        await axios.post(`${API}/produtos`, data);
      }
      
      fetchProdutos();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      console.error('Erro ao salvar produto:', error);
      alert('Erro ao salvar produto');
    }
  };

  const handleEdit = (produto) => {
    setEditingProduto(produto);
    setFormData({
      sku: produto.sku,
      ean: produto.ean || '',
      nome: produto.nome,
      descricao: produto.descricao || '',
      categoria: produto.categoria || '',
      marca: produto.marca || '',
      unidade: produto.unidade || 'UN',
      valor_compra: produto.valor_compra || 0,
      preco_venda: produto.preco_venda || 0,
      fornecedor_id: produto.fornecedor_id || '',
      fora_estado: produto.fora_estado || false
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Tem certeza que deseja deletar este produto?')) {
      try {
        await axios.delete(`${API}/produtos/${id}`);
        fetchProdutos();
      } catch (error) {
        console.error('Erro ao deletar produto:', error);
        alert('Erro ao deletar produto');
      }
    }
  };

  const handleViewMovimentacoes = async (produto) => {
    setViewingMovimentacoes(produto);
    await fetchMovimentacoes(produto.id);
    setMovimentacaoDialogOpen(true);
  };

  const resetForm = () => {
    setEditingProduto(null);
    setFormData({
      sku: '',
      ean: '',
      nome: '',
      descricao: '',
      categoria: '',
      marca: '',
      unidade: 'UN',
      valor_compra: 0,
      preco_venda: 0,
      fornecedor_id: '',
      fora_estado: false
    });
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: type === 'checkbox' ? checked : value 
    }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  const getEstoqueBadge = (estoque) => {
    if (estoque === 0) {
      return <Badge variant="secondary">Sem estoque</Badge>;
    } else if (estoque < 0) {
      return <Badge variant="destructive">Negativo ({estoque})</Badge>;
    } else if (estoque <= 10) {
      return <Badge variant="secondary">Baixo ({estoque})</Badge>;
    } else {
      return <Badge variant="default">OK ({estoque})</Badge>;
    }
  };

  const getFornecedorNome = (fornecedorId) => {
    const fornecedor = fornecedores.find(f => f.id === fornecedorId);
    return fornecedor ? fornecedor.nome : 'N/A';
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
          <h1 className="text-3xl font-bold text-gray-900">Produtos</h1>
          <p className="text-gray-600">Gerencie seu catálogo de produtos com estoque multi-CNPJ</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="mr-2 h-4 w-4" />
              Novo Produto
            </Button>
          </DialogTrigger>
          
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingProduto ? 'Editar Produto' : 'Novo Produto'}
              </DialogTitle>
              <DialogDescription>
                {editingProduto ? 'Atualize as informações do produto' : 'Adicione um novo produto ao catálogo'}
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input
                    id="sku"
                    name="sku"
                    value={formData.sku}
                    onChange={handleInputChange}
                    placeholder="Código do produto"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="ean">EAN</Label>
                  <Input
                    id="ean"
                    name="ean"
                    value={formData.ean}
                    onChange={handleInputChange}
                    placeholder="Código de barras"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="nome">Nome do Produto *</Label>
                <Input
                  id="nome"
                  name="nome"
                  value={formData.nome}
                  onChange={handleInputChange}
                  placeholder="Nome do produto"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="descricao">Descrição</Label>
                <Textarea
                  id="descricao"
                  name="descricao"
                  value={formData.descricao}
                  onChange={handleInputChange}
                  placeholder="Descrição detalhada do produto"
                  rows={3}
                />
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="categoria">Categoria</Label>
                  <Input
                    id="categoria"
                    name="categoria"
                    value={formData.categoria}
                    onChange={handleInputChange}
                    placeholder="Categoria"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="marca">Marca</Label>
                  <Input
                    id="marca"
                    name="marca"
                    value={formData.marca}
                    onChange={handleInputChange}
                    placeholder="Marca"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="unidade">Unidade</Label>
                  <Select value={formData.unidade} onValueChange={(value) => setFormData(prev => ({...prev, unidade: value}))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="UN">UN - Unidade</SelectItem>
                      <SelectItem value="KG">KG - Quilograma</SelectItem>
                      <SelectItem value="MT">MT - Metro</SelectItem>
                      <SelectItem value="LT">LT - Litro</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="valor_compra">Valor de Compra</Label>
                  <Input
                    id="valor_compra"
                    name="valor_compra"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.valor_compra}
                    onChange={handleInputChange}
                    placeholder="0.00"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="preco_venda">Preço de Venda</Label>
                  <Input
                    id="preco_venda"
                    name="preco_venda"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.preco_venda}
                    onChange={handleInputChange}
                    placeholder="0.00"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="fornecedor_id">Fornecedor</Label>
                <Select value={formData.fornecedor_id} onValueChange={(value) => setFormData(prev => ({...prev, fornecedor_id: value}))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione um fornecedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {fornecedores.map((fornecedor) => (
                      <SelectItem key={fornecedor.id} value={fornecedor.id}>
                        {fornecedor.nome}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="fora_estado"
                  name="fora_estado"
                  checked={formData.fora_estado}
                  onChange={handleInputChange}
                  className="rounded"
                />
                <Label htmlFor="fora_estado">
                  Produto de fora do estado (adicional ICMS 6%)
                </Label>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancelar
                </Button>
                <Button type="submit">
                  {editingProduto ? 'Atualizar' : 'Salvar'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Produtos</CardTitle>
          <CardDescription>
            Total de {produtos.length} produto(s) cadastrado(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {produtos.length === 0 ? (
            <div className="text-center py-8">
              <Package className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">Nenhum produto cadastrado</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Img</TableHead>
                    <TableHead>SKU / Nome</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead>Fornecedor</TableHead>
                    <TableHead>Custo Médio</TableHead>
                    <TableHead>Preço Venda</TableHead>
                    <TableHead>Estoque Total</TableHead>
                    <TableHead>Estoques CNPJ</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {produtos.map((produto) => (
                    <TableRow key={produto.id}>
                      <TableCell>
                        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center">
                          {produto.imagem_url ? (
                            <img src={produto.imagem_url} alt={produto.nome} className="w-full h-full object-cover rounded" />
                          ) : (
                            <Image className="h-6 w-6 text-gray-400" />
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{produto.nome}</div>
                          <div className="text-sm text-gray-500">SKU: {produto.sku}</div>
                          {produto.ean && <div className="text-xs text-gray-400">EAN: {produto.ean}</div>}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div>{produto.categoria}</div>
                          <div className="text-sm text-gray-500">{produto.marca}</div>
                        </div>
                      </TableCell>
                      <TableCell>{getFornecedorNome(produto.fornecedor_id)}</TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(produto.custo_medio)}
                      </TableCell>
                      <TableCell className="font-medium text-green-600">
                        {formatCurrency(produto.preco_venda)}
                      </TableCell>
                      <TableCell>
                        {getEstoqueBadge(produto.estoque_total)}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          {produto.estoques_cnpj?.map((estoque) => (
                            <div key={estoque.cnpj} className="text-xs">
                              <span className="font-medium">{CNPJS_CONFIG[estoque.cnpj]}:</span>
                              <span className={`ml-1 ${estoque.quantidade < 0 ? 'text-red-600' : estoque.quantidade === 0 ? 'text-gray-500' : 'text-green-600'}`}>
                                {estoque.quantidade}
                              </span>
                            </div>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end space-x-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleViewMovimentacoes(produto)}
                            title="Ver movimentações"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEdit(produto)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDelete(produto.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dialog de Movimentações */}
      <Dialog open={movimentacaoDialogOpen} onOpenChange={setMovimentacaoDialogOpen}>
        <DialogContent className="sm:max-w-6xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Movimentações de Estoque - {viewingMovimentacoes?.nome}
            </DialogTitle>
            <DialogDescription>
              SKU: {viewingMovimentacoes?.sku} | Estoque Total: {viewingMovimentacoes?.estoque_total} unidades
            </DialogDescription>
          </DialogHeader>
          
          {/* Resumo */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <Card>
              <CardContent className="pt-4">
                <div className="text-2xl font-bold text-green-600">{resumoMovimentacoes.total_entradas || 0}</div>
                <p className="text-sm text-gray-600">Total Entradas</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-2xl font-bold text-red-600">{resumoMovimentacoes.total_saidas || 0}</div>
                <p className="text-sm text-gray-600">Total Saídas</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className={`text-2xl font-bold ${(resumoMovimentacoes.saldo || 0) >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {resumoMovimentacoes.saldo || 0}
                </div>
                <p className="text-sm text-gray-600">Saldo</p>
              </CardContent>
            </Card>
          </div>

          {/* Lista de Movimentações */}
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>CNPJ</TableHead>
                  <TableHead>Documento</TableHead>
                  <TableHead>Entrada</TableHead>
                  <TableHead>Saída</TableHead>
                  <TableHead>Valor Unit.</TableHead>
                  <TableHead>Usuário</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {movimentacoes.map((mov, index) => (
                  <TableRow key={index}>
                    <TableCell>{formatDate(mov.data)}</TableCell>
                    <TableCell>
                      <Badge variant={mov.tipo === 'COMPRA' ? 'default' : mov.tipo === 'VENDA' ? 'secondary' : 'outline'}>
                        {mov.tipo}
                      </Badge>
                    </TableCell>
                    <TableCell>{CNPJS_CONFIG[mov.cnpj] || mov.cnpj}</TableCell>
                    <TableCell>{mov.documento}</TableCell>
                    <TableCell className="text-green-600 font-medium">
                      {mov.quantidade_entrada > 0 ? mov.quantidade_entrada : '-'}
                    </TableCell>
                    <TableCell className="text-red-600 font-medium">
                      {mov.quantidade_saida > 0 ? mov.quantidade_saida : '-'}
                    </TableCell>
                    <TableCell>{formatCurrency(mov.valor_unitario)}</TableCell>
                    <TableCell>{mov.usuario}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Produtos;