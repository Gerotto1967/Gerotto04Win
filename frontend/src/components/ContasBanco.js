import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Plus, CreditCard, Building, DollarSign } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ContasBanco = () => {
  const [contas, setContas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingConta, setEditingConta] = useState(null);
  const [formData, setFormData] = useState({
    nome: '',
    tipo: '',
    banco: '',
    agencia: '',
    conta: '',
    saldo_atual: 0
  });

  useEffect(() => {
    fetchContas();
  }, []);

  const fetchContas = async () => {
    try {
      const response = await axios.get(`${API}/contas-banco`);
      setContas(response.data);
    } catch (error) {
      console.error('Erro ao carregar contas:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        saldo_atual: parseFloat(formData.saldo_atual)
      };

      if (editingConta) {
        await axios.put(`${API}/contas-banco/${editingConta.id}`, data);
      } else {
        await axios.post(`${API}/contas-banco`, data);
      }
      
      fetchContas();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      console.error('Erro ao salvar conta:', error);
      alert('Erro ao salvar conta');
    }
  };

  const handleEdit = (conta) => {
    setEditingConta(conta);
    setFormData({
      nome: conta.nome,
      tipo: conta.tipo,
      banco: conta.banco || '',
      agencia: conta.agencia || '',
      conta: conta.conta || '',
      saldo_atual: conta.saldo_atual
    });
    setIsDialogOpen(true);
  };

  const resetForm = () => {
    setEditingConta(null);
    setFormData({
      nome: '',
      tipo: '',
      banco: '',
      agencia: '',
      conta: '',
      saldo_atual: 0
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

  const getTipoBadge = (tipo) => {
    const tipos = {
      'BANCO': { variant: 'default', label: 'Banco' },
      'CAIXA': { variant: 'secondary', label: 'Caixa' },
      'POUPANCA': { variant: 'outline', label: 'Poupança' },
      'CARTAO': { variant: 'destructive', label: 'Cartão' }
    };
    
    const config = tipos[tipo] || { variant: 'default', label: tipo };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  const totalSaldo = contas.reduce((total, conta) => total + conta.saldo_atual, 0);

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
          <h1 className="text-3xl font-bold text-gray-900">Contas Bancárias</h1>
          <p className="text-gray-600">Gerencie suas contas bancárias e saldos</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={resetForm}>
              <Plus className="mr-2 h-4 w-4" />
              Nova Conta
            </Button>
          </DialogTrigger>
          
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {editingConta ? 'Editar Conta' : 'Nova Conta Bancária'}
              </DialogTitle>
              <DialogDescription>
                {editingConta ? 'Atualize as informações da conta' : 'Adicione uma nova conta bancária'}
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="nome">Nome da Conta *</Label>
                <Input
                  id="nome"
                  name="nome"
                  value={formData.nome}
                  onChange={handleInputChange}
                  placeholder="Ex: Conta Corrente Santander"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="tipo">Tipo *</Label>
                <Select value={formData.tipo} onValueChange={(value) => setFormData(prev => ({...prev, tipo: value}))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BANCO">Conta Bancária</SelectItem>
                    <SelectItem value="CAIXA">Caixa</SelectItem>
                    <SelectItem value="POUPANCA">Poupança</SelectItem>
                    <SelectItem value="CARTAO">Cartão</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="banco">Banco</Label>
                <Input
                  id="banco"
                  name="banco"
                  value={formData.banco}
                  onChange={handleInputChange}
                  placeholder="Nome do banco"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="agencia">Agência</Label>
                  <Input
                    id="agencia"
                    name="agencia"
                    value={formData.agencia}
                    onChange={handleInputChange}
                    placeholder="0000"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="conta">Conta</Label>
                  <Input
                    id="conta"
                    name="conta"
                    value={formData.conta}
                    onChange={handleInputChange}
                    placeholder="00000-0"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="saldo_atual">Saldo Atual</Label>
                <Input
                  id="saldo_atual"
                  name="saldo_atual"
                  type="number"
                  step="0.01"
                  value={formData.saldo_atual}
                  onChange={handleInputChange}
                  placeholder="0.00"
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
                  {editingConta ? 'Atualizar' : 'Salvar'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Card de resumo */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <DollarSign className="mr-2 h-5 w-5" />
            Resumo Financeiro
          </CardTitle>
          <CardDescription>
            Saldo total de todas as contas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className={`text-3xl font-bold ${totalSaldo >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatCurrency(totalSaldo)}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            {contas.length} conta(s) cadastrada(s)
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Lista de Contas</CardTitle>
          <CardDescription>
            Todas as contas bancárias cadastradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          {contas.length === 0 ? (
            <div className="text-center py-8">
              <CreditCard className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-500">Nenhuma conta cadastrada</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Banco</TableHead>
                    <TableHead>Agência / Conta</TableHead>
                    <TableHead>Saldo</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {contas.map((conta) => (
                    <TableRow key={conta.id}>
                      <TableCell>
                        <div className="flex items-center">
                          <CreditCard className="mr-2 h-4 w-4 text-gray-400" />
                          <div className="font-medium">{conta.nome}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getTipoBadge(conta.tipo)}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center">
                          <Building className="mr-2 h-4 w-4 text-gray-400" />
                          {conta.banco || '-'}
                        </div>
                      </TableCell>
                      <TableCell>
                        {conta.agencia && conta.conta ? (
                          <div className="font-mono text-sm">
                            {conta.agencia} / {conta.conta}
                          </div>
                        ) : '-'}
                      </TableCell>
                      <TableCell>
                        <div className={`font-bold ${
                          conta.saldo_atual >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(conta.saldo_atual)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          conta.ativo 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {conta.ativo ? 'Ativa' : 'Inativa'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEdit(conta)}
                        >
                          Editar
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
    </div>
  );
};

export default ContasBanco;