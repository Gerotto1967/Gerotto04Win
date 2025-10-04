import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";

// Components
import LoginPage from "./components/LoginPage";
import Layout from "./components/Layout";
import Dashboard from "./components/Dashboard";
import Clientes from "./components/Clientes";
import Fornecedores from "./components/Fornecedores";
import Produtos from "./components/Produtos";
import Estoque from "./components/Estoque";
import Financeiro from "./components/Financeiro";
import ContasBanco from "./components/ContasBanco";
import ProcessarXML from "./components/ProcessarXML";
import UpselllerIntegration from "./components/UpselllerIntegration";
import Empresas from "./components/Empresas";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configurar interceptador do axios para adicionar token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptador de resposta para tratar token expirado
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
        setIsAuthenticated(true);
      } catch (error) {
        localStorage.removeItem('token');
        setIsAuthenticated(false);
      }
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: username,
        password
      });
      
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      setUser(user);
      setIsAuthenticated(true);
      return true;
    } catch (error) {
      console.error('Erro no login:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
                <Navigate to="/dashboard" replace /> : 
                <LoginPage onLogin={login} />
            } 
          />
          
          {isAuthenticated ? (
            <Route path="/" element={<Layout user={user} onLogout={logout} />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="empresas" element={<Empresas />} />
              <Route path="clientes" element={<Clientes />} />
              <Route path="fornecedores" element={<Fornecedores />} />
              <Route path="produtos" element={<Produtos />} />
              <Route path="estoque" element={<Estoque />} />
              <Route path="financeiro" element={<Financeiro />} />
              <Route path="contas-banco" element={<ContasBanco />} />
              <Route path="processar-xml" element={<ProcessarXML />} />
              <Route path="upseller" element={<UpselllerIntegration />} />
            </Route>
          ) : (
            <Route path="*" element={<Navigate to="/login" replace />} />
          )}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;