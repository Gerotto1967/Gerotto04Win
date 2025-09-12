import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Upload, FileText, Package, DollarSign, AlertTriangle } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CNPJS_CONFIG = {
  "11111111000101": "EMPRESA ABC LTDA",
  "22222222000102": "EMPRESA XYZ LTDA", 
  "33333333000103": "EMPRESA 123 LTDA",
  "44444444000104": "EMPRESA DEF LTDA",
  "55555555000105": "EMPRESA GHI LTDA"
};

const ProcessarXML = () => {
  const [arquivo, setArquivo] = useState(null);
  const [cnpjDestino, setCnpjDestino] = useState('');
  const [dadosXML, setDadosXML] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.xml')) {
      setArquivo(file);
      setUploadSuccess(false);
      setDadosXML(null);
    } else {
      alert('Por favor, selecione um arquivo XML válido');
      e.target.value = '';
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    
    if (!arquivo) {
      alert('Selecione um arquivo XML');
      return;
    }
    
    if (!cnpjDestino) {
      alert('Selecione o CNPJ de destino');
      return;
    }

    setLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      formData.append('cnpj_destino', cnpjDestino);

      const response = await axios.post(`${API}/xml/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setDadosXML(response.data.dados);
      setUploadSuccess(true);
      
    } catch (error) {
      console.error('Erro ao fazer upload do XML:', error);
      alert('Erro ao processar XML: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleProcessar = async () => {
    if (!dadosXML) return;

    setLoading(true);
    
    try {
      await axios.post(`${API}/xml/${dadosXML._id}/processar`);
      alert('XML processado com sucesso! Estoque e financeiro foram atualizados.');
      
      // Reset form
      setArquivo(null);
      setCnpjDestino('');
      setDadosXML(null);
      setUploadSuccess(false);
      document.getElementById('file-input').value = '';
      
    } catch (error) {
      console.error('Erro ao processar XML:', error);
      alert('Erro ao processar XML: ' + (error.response?.data?.detail || error.message));
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Processar XML de Compra</h1>
        <p className="text-gray-600">Upload e processamento de notas fiscais XML</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card de Upload */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Upload className="mr-2 h-5 w-5" />
              Upload de XML
            </CardTitle>
            <CardDescription>
              Selecione o arquivo XML da nota fiscal e o CNPJ de destino
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="file-input">Arquivo XML *</Label>
                <Input
                  id="file-input"
                  type="file"
                  accept=".xml"
                  onChange={handleFileChange}
                  required
                  className="cursor-pointer"
                />
                <p className="text-xs text-gray-500">
                  Apenas arquivos XML de nota fiscal são aceitos
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cnpj-destino">CNPJ de Destino *</Label>
                <Select value={cnpjDestino} onValueChange={setCnpjDestino}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione o CNPJ que receberá os produtos" />
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

              <Button type="submit" disabled={loading || uploadSuccess} className="w-full">
                {loading ? 'Processando...' : uploadSuccess ? 'XML Processado' : 'Analisar XML'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Card de Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="mr-2 h-5 w-5" />
              Status do Processamento
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!uploadSuccess && !dadosXML && (
              <div className="text-center py-8">
                <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <p className="text-gray-500">Nenhum XML processado ainda</p>
              </div>
            )}

            {uploadSuccess && dadosXML && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  <Badge className="bg-green-100 text-green-800">XML Analisado</Badge>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Fornecedor:</span>
                    <span className="font-medium">{dadosXML.fornecedor_nome}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>CNPJ:</span>
                    <span className="font-mono">{dadosXML.fornecedor_cnpj}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Nota Fiscal:</span>
                    <span className="font-medium">{dadosXML.numero_nf}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Valor Total:</span>
                    <span className="font-bold text-green-600">
                      {formatCurrency(dadosXML.valor_total)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Itens:</span>
                    <span className="font-medium">{dadosXML.itens?.length || 0} produtos</span>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <Button 
                    onClick={handleProcessar} 
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? 'Integrando...' : 'Confirmar e Integrar ao Sistema'}
                  </Button>
                  <p className="text-xs text-gray-500 mt-2 text-center">
                    Isto irá atualizar o estoque e criar conta a pagar
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabela de Itens do XML */}
      {dadosXML && dadosXML.itens && dadosXML.itens.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Package className="mr-2 h-5 w-5" />
              Itens da Nota Fiscal
            </CardTitle>
            <CardDescription>
              {dadosXML.itens.length} item(ns) encontrado(s) no XML
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead>EAN</TableHead>
                    <TableHead className="text-right">Quantidade</TableHead>
                    <TableHead className="text-right">Valor Unit.</TableHead>
                    <TableHead className="text-right">Valor Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {dadosXML.itens.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-mono text-sm">{item.codigo}</TableCell>
                      <TableCell>
                        <div className="max-w-xs">
                          <div className="font-medium truncate">{item.descricao}</div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{item.ean || '-'}</TableCell>
                      <TableCell className="text-right font-medium">
                        {item.quantidade}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(item.valor_unitario)}
                      </TableCell>
                      <TableCell className="text-right font-bold">
                        {formatCurrency(item.valor_total)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="text-lg font-medium">Total dos Produtos:</span>
                <span className="text-xl font-bold text-green-600">
                  {formatCurrency(dadosXML.valor_produtos)}
                </span>
              </div>
              {dadosXML.valor_icms > 0 && (
                <div className="flex justify-between items-center text-sm text-gray-600">
                  <span>ICMS:</span>
                  <span>{formatCurrency(dadosXML.valor_icms)}</span>
                </div>
              )}
              <div className="flex justify-between items-center text-lg font-bold border-t pt-2 mt-2">
                <span>Total da Nota:</span>
                <span className="text-green-600">{formatCurrency(dadosXML.valor_total)}</span>
              </div>
            </div>

            {/* Avisos importantes */}
            <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
              <div className="flex items-start">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-yellow-800 mb-1">Atenções importantes:</p>
                  <ul className="text-yellow-700 space-y-1">
                    <li>• Os produtos serão adicionados ao estoque do CNPJ: <strong>{CNPJS_CONFIG[cnpjDestino]}</strong></li>
                    <li>• Será criada uma conta a pagar no valor total da nota</li>
                    <li>• Produtos de fora do estado terão adicional de 6% ICMS aplicado automaticamente</li>
                    <li>• O custo médio dos produtos será recalculado</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProcessarXML;