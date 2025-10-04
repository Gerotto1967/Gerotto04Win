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
import { Plus, DollarSign, TrendingUp, TrendingDown, CreditCard, Calendar } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Financeiro = () => {
  const [contas, setContas] = useState([]);
  const [contasBanco, setContasBanco] = useState([]);
  const [fornecedores, setFornecedores] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [relatorio, setRelatorio] = useState({});
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [filtroTipo, setFiltroTipo] = useState(null);
  const [filtroStatus, setFiltroStatus] = useState(null);
  const [formData, setFormData] = useState({
    tipo: '',
    descricao: '',
    valor: 0,
    data_vencimento: '',
    categoria: '',
    observacoes: '',
    fornecedor_id: '',
    cliente_id: '',
    documento: '',
    cnpj: '',
    parcelas: 1
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      await Promise.all([
        fetchContas(),
        fetchContasBanco(),
        fetchFornecedores(),
        fetchClientes(),
        fetchRelatorio()
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/financeiro`);
      setContas(response.data);
    } catch (error) {
      console.error('Erro ao carregar contas:', error);
    }
  };

  const fetchContasBanco = async () => {
    try {
      const response = await axios.get(`${API}/contas-banco`);
      setContasBanco(response.data);
    } catch (error) {
      console.error('Erro ao carregar contas banco:', error);
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

  const fetchClientes = async () => {
    try {
      const response = await axios.get(`${API}/clientes`);
      setClientes(response.data);
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
    }
  };

  const fetchRelatorio = async () => {
    try {
      const response = await axios.get(`${API}/financeiro/relatorios`);
      setRelatorio(response.data);
    } catch (error) {
      console.error('Erro ao carregar relatórios:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/financeiro`, formData);
      fetchData();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      console.error('Erro ao salvar conta:', error);
      alert('Erro ao salvar conta');
    }
  };

  const handlePagar = async (contaId, valor, dataPagamento, contaBancoId) => {
    try {
      await axios.post(`${API}/financeiro/${contaId}/pagar`, {
        conta_banco_id: contaBancoId,
        valor_pago: valor,
        data_pagamento: dataPagamento
      });
      fetchData();
    } catch (error) {
      console.error('Erro ao pagar conta:', error);
      alert('Erro ao pagar conta');
    }
  };

  const resetForm = () => {
    setFormData({
      tipo: '',
      descricao: '',
      valor: 0,
      data_vencimento: '',
      categoria: '',
      observacoes: '',
      fornecedor_id: '',
      cliente_id: '',
      documento: '',
      cnpj: '',
      parcelas: 1
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
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

  const getStatusBadge = (status, dataVencimento) => {
    const hoje = new Date();
    const vencimento = new Date(dataVencimento);
    
    if (status === 'PAGO') {
      return <Badge className="bg-green-100 text-green-800">Pago</Badge>;
    } else if (vencimento < hoje) {
      return <Badge variant="destructive">Vencido</Badge>;
    } else {
      return <Badge variant="secondary">Pendente</Badge>;
    }
  };

  const contasFiltradas = contas.filter(conta => {
    const filtroTipoOk = !filtroTipo || conta.tipo === filtroTipo;
    const filtroStatusOk = !filtroStatus || conta.status === filtroStatus;
    return filtroTipoOk && filtroStatusOk;
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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Financeiro</h1>
          <p className="text-gray-600">Controle de contas a pagar e receber</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="mr-2 h-4 w-4" />
              Nova Conta
            </Button>
          </DialogTrigger>
          
          <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Nova Conta</DialogTitle>
              <DialogDescription>
                Adicione uma nova conta a pagar ou receber
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="tipo">Tipo *</Label>
                  <Select onValueChange={(value) => setFormData(prev => ({...prev, tipo: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione o tipo" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PAGAR">Conta a Pagar</SelectItem>
                      <SelectItem value="RECEBER">Conta a Receber</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="categoria">Categoria</Label>
                  <Input
                    id="categoria"
                    name="categoria"
                    value={formData.categoria}
                    onChange={handleInputChange}
                    placeholder="Ex: Aluguel, Vendas, Compras"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="descricao">Descrição *</Label>
                <Input
                  id="descricao"
                  name="descricao"
                  value={formData.descricao}
                  onChange={handleInputChange}
                  placeholder="Descrição da conta"
                  required
                />
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="valor">Valor *</Label>
                  <Input
                    id="valor"
                    name="valor"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.valor}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="data_vencimento">Data Vencimento *</Label>
                  <Input
                    id="data_vencimento"
                    name="data_vencimento"
                    type="date"
                    value={formData.data_vencimento}
                    onChange={handleInputChange}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="parcelas">Parcelas</Label>
                  <Input
                    id="parcelas"
                    name="parcelas"
                    type="number"
                    min="1"
                    value={formData.parcelas}
                    onChange={handleInputChange}
                    placeholder="1"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="documento">Documento</Label>
                  <Input
                    id="documento"
                    name="documento"
                    value={formData.documento}
                    onChange={handleInputChange}
                    placeholder="Número do documento"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="cnpj">CNPJ</Label>
                  <Input
                    id="cnpj"
                    name="cnpj"
                    value={formData.cnpj}
                    onChange={handleInputChange}
                    placeholder="CNPJ relacionado"
                  />
                </div>
              </div>
              
              {formData.tipo === 'PAGAR' && (
                <div className="space-y-2">
                  <Label htmlFor="fornecedor_id">Fornecedor</Label>
                  <Select onValueChange={(value) => setFormData(prev => ({...prev, fornecedor_id: value}))}>
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
              )}
              
              {formData.tipo === 'RECEBER' && (
                <div className="space-y-2">
                  <Label htmlFor="cliente_id">Cliente</Label>
                  <Select onValueChange={(value) => setFormData(prev => ({...prev, cliente_id: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecione um cliente" />
                    </SelectTrigger>
                    <SelectContent>
                      {clientes.map((cliente) => (
                        <SelectItem key={cliente.id} value={cliente.id}>
                          {cliente.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="observacoes">Observações</Label>
                <Textarea
                  id="observacoes"
                  name="observacoes"
                  value={formData.observacoes}
                  onChange={handleInputChange}
                  placeholder="Observações adicionais"
                  rows={3}
                />
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
                  Salvar
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Cards de resumo */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contas a Pagar</CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {formatCurrency(relatorio.contas_pagar || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Contas a Receber</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(relatorio.contas_receber || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Saldo Bancos</CardTitle>
            <CreditCard className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(relatorio.saldo_bancos || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Patrimônio Líquido</CardTitle>
            <DollarSign className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${
              (relatorio.patrimonio_liquido || 0) >= 0 ? 'text-emerald-600' : 'text-red-600'
            }`}>
              {formatCurrency(relatorio.patrimonio_liquido || 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contas Financeiras</CardTitle>
          <CardDescription>
            Lista de contas a pagar e receber - {contasFiltradas.length} conta(s)
          </CardDescription>
          <div className="flex items-center space-x-2">
            <Select value={filtroTipo || undefined} onValueChange={setFiltroTipo}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Todos os tipos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={null}>Todos os tipos</SelectItem>
                <SelectItem value="PAGAR">A Pagar</SelectItem>
                <SelectItem value="RECEBER">A Receber</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filtroStatus || undefined} onValueChange={setFiltroStatus}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Todos status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Todos status</SelectItem>
                <SelectItem value="PENDENTE">Pendente</SelectItem>
                <SelectItem value="PAGO">Pago</SelectItem>
                <SelectItem value="VENCIDO">Vencido</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {contasFiltradas.length === 0 ? (
            <div className="text-center py-8">
              <DollarSign className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">Nenhuma conta encontrada</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Vencimento</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contasFiltradas.map((conta) => (
                    <TableRow key={conta.id}>
                      <TableCell>
                        <Badge variant={conta.tipo === 'PAGAR' ? 'destructive' : 'default'}>
                          {conta.tipo === 'PAGAR' ? 'A Pagar' : 'A Receber'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{conta.descricao}</div>
                          {conta.documento && (
                            <div className="text-sm text-gray-500">Doc: {conta.documento}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-medium">
                        {formatCurrency(conta.valor)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Calendar className="mr-2 h-4 w-4 text-gray-400" />
                          {formatDate(conta.data_vencimento)}
                        </div>
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(conta.status, conta.data_vencimento)}
                      </TableCell>
                      <TableCell>{conta.categoria}</TableCell>
                      <TableCell className="text-right">
                        {conta.status === 'PENDENTE' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const dataPagamento = new Date().toISOString().split('T')[0];
                              const contaBancoId = prompt('ID da conta banco:');
                              if (contaBancoId) {
                                handlePagar(conta.id, conta.valor, dataPagamento, contaBancoId);
                              }
                            }}
                          >
                            Pagar
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Financeiro;