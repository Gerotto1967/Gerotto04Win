#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for ERP System
Tests PostgreSQL migration and all CRUD operations
"""

import requests
import json
import sys
from datetime import datetime, date

# API Configuration
BASE_URL = "https://erpsystem-4.preview.emergentagent.com/api"
AUTH_EMAIL = "admin"
AUTH_PASSWORD = "admin123"

class ERPTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        
    def log_test(self, test_name, success, message="", data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
        
    def authenticate(self):
        """Test authentication and get token"""
        try:
            auth_data = {
                "email": AUTH_EMAIL,
                "password": AUTH_PASSWORD
            }
            
            response = requests.post(f"{self.base_url}/auth/login", json=auth_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers["Authorization"] = f"Bearer {self.token}"
                self.log_test("Authentication", True, f"Login successful for {AUTH_EMAIL}")
                return True
            else:
                self.log_test("Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_auth_me(self):
        """Test /auth/me endpoint"""
        try:
            response = requests.get(f"{self.base_url}/auth/me", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Auth Me", True, f"User info retrieved: {data.get('email')}")
                return True
            else:
                self.log_test("Auth Me", False, f"Failed to get user info: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Auth Me", False, f"Error: {str(e)}")
            return False
    
    def test_empresas_crud(self):
        """Test complete CRUD operations for Empresas"""
        empresa_id = None
        
        # Test data from review request
        empresa_data = {
            "cnpj": "12.345.678/0001-99",
            "razao_social": "Teste Backend Ltda",
            "nome_fantasia": "Backend Test",
            "uf": "RJ",
            "endereco": "Rua Teste, 123",
            "cidade": "Rio de Janeiro",
            "cep": "20000-000",
            "telefone": "(21) 99999-9999",
            "email": "teste@backend.com"
        }
        
        try:
            # CREATE - POST /empresas
            response = requests.post(f"{self.base_url}/empresas", json=empresa_data, headers=self.headers)
            
            if response.status_code == 200:
                created_empresa = response.json()
                empresa_id = created_empresa.get("id")
                self.log_test("Empresas CREATE", True, f"Empresa created with ID: {empresa_id}")
            else:
                self.log_test("Empresas CREATE", False, f"Failed to create empresa: {response.status_code} - {response.text}")
                return False
            
            # READ - GET /empresas (list all)
            response = requests.get(f"{self.base_url}/empresas", headers=self.headers)
            
            if response.status_code == 200:
                empresas = response.json()
                self.log_test("Empresas READ (List)", True, f"Retrieved {len(empresas)} empresas")
            else:
                self.log_test("Empresas READ (List)", False, f"Failed to list empresas: {response.status_code}")
            
            # READ - GET /empresas/{id} (get specific)
            if empresa_id:
                response = requests.get(f"{self.base_url}/empresas/{empresa_id}", headers=self.headers)
                
                if response.status_code == 200:
                    empresa = response.json()
                    self.log_test("Empresas READ (Single)", True, f"Retrieved empresa: {empresa.get('razao_social')}")
                else:
                    self.log_test("Empresas READ (Single)", False, f"Failed to get empresa: {response.status_code}")
            
            # UPDATE - PUT /empresas/{id}
            if empresa_id:
                update_data = empresa_data.copy()
                update_data["nome_fantasia"] = "Backend Test Updated"
                
                response = requests.put(f"{self.base_url}/empresas/{empresa_id}", json=update_data, headers=self.headers)
                
                if response.status_code == 200:
                    updated_empresa = response.json()
                    self.log_test("Empresas UPDATE", True, f"Empresa updated: {updated_empresa.get('nome_fantasia')}")
                else:
                    self.log_test("Empresas UPDATE", False, f"Failed to update empresa: {response.status_code}")
            
            # DELETE - DELETE /empresas/{id}
            if empresa_id:
                response = requests.delete(f"{self.base_url}/empresas/{empresa_id}", headers=self.headers)
                
                if response.status_code == 200:
                    self.log_test("Empresas DELETE", True, "Empresa deleted successfully")
                else:
                    self.log_test("Empresas DELETE", False, f"Failed to delete empresa: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Empresas CRUD", False, f"Error during CRUD operations: {str(e)}")
            return False
    
    def test_clientes_api(self):
        """Test Clientes API endpoints"""
        try:
            # Test GET /clientes
            response = requests.get(f"{self.base_url}/clientes", headers=self.headers)
            
            if response.status_code == 200:
                clientes = response.json()
                self.log_test("Clientes API", True, f"Retrieved {len(clientes)} clientes")
                return True
            else:
                self.log_test("Clientes API", False, f"Failed to get clientes: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Clientes API", False, f"Error: {str(e)}")
            return False
    
    def test_fornecedores_api(self):
        """Test Fornecedores API endpoints"""
        try:
            # Test GET /fornecedores
            response = requests.get(f"{self.base_url}/fornecedores", headers=self.headers)
            
            if response.status_code == 200:
                fornecedores = response.json()
                self.log_test("Fornecedores API", True, f"Retrieved {len(fornecedores)} fornecedores")
                return True
            else:
                self.log_test("Fornecedores API", False, f"Failed to get fornecedores: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Fornecedores API", False, f"Error: {str(e)}")
            return False
    
    def test_produtos_api(self):
        """Test Produtos API endpoints"""
        try:
            # Test GET /produtos
            response = requests.get(f"{self.base_url}/produtos", headers=self.headers)
            
            if response.status_code == 200:
                produtos = response.json()
                self.log_test("Produtos API", True, f"Retrieved {len(produtos)} produtos")
                return True
            else:
                self.log_test("Produtos API", False, f"Failed to get produtos: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Produtos API", False, f"Error: {str(e)}")
            return False
    
    def test_financeiro_api(self):
        """Test Financeiro API endpoints"""
        try:
            # Test GET /financeiro/contas
            response = requests.get(f"{self.base_url}/financeiro/contas", headers=self.headers)
            
            if response.status_code == 200:
                contas = response.json()
                self.log_test("Financeiro API", True, f"Retrieved {len(contas)} contas financeiras")
                return True
            else:
                self.log_test("Financeiro API", False, f"Failed to get contas: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Financeiro API", False, f"Error: {str(e)}")
            return False
    
    def test_contas_banco_api(self):
        """Test Contas Banco API endpoints"""
        try:
            # Test GET /contas-banco
            response = requests.get(f"{self.base_url}/contas-banco", headers=self.headers)
            
            if response.status_code == 200:
                contas = response.json()
                self.log_test("Contas Banco API", True, f"Retrieved {len(contas)} contas bancárias")
                return True
            else:
                self.log_test("Contas Banco API", False, f"Failed to get contas banco: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Contas Banco API", False, f"Error: {str(e)}")
            return False
    
    def test_dashboard_stats(self):
        """Test Dashboard Statistics"""
        try:
            response = requests.get(f"{self.base_url}/dashboard/stats", headers=self.headers)
            
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Dashboard Stats", True, f"Stats retrieved: {json.dumps(stats, indent=2)}")
                return True
            else:
                self.log_test("Dashboard Stats", False, f"Failed to get dashboard stats: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Dashboard Stats", False, f"Error: {str(e)}")
            return False
    
    def test_root_endpoint(self):
        """Test root endpoint to verify API is running"""
        try:
            # Remove /api from base URL for root endpoint
            root_url = self.base_url.replace('/api', '')
            response = requests.get(root_url)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Root Endpoint", True, f"API Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_test("Root Endpoint", False, f"Root endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚀 Starting ERP System Backend API Tests")
        print("=" * 60)
        print(f"Testing API at: {self.base_url}")
        print(f"Authentication: {AUTH_EMAIL}")
        print("=" * 60)
        
        # Test API availability
        self.test_root_endpoint()
        
        # Authentication is required for all other tests
        if not self.authenticate():
            print("\n❌ Authentication failed - stopping tests")
            return False
        
        # Test authenticated user info
        self.test_auth_me()
        
        # Test all main API endpoints
        self.test_empresas_crud()
        self.test_clientes_api()
        self.test_fornecedores_api()
        self.test_produtos_api()
        self.test_financeiro_api()
        self.test_contas_banco_api()
        self.test_dashboard_stats()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 All tests passed! PostgreSQL migration successful!")
            return True
        else:
            print(f"\n⚠️  {total - passed} tests failed. Check logs above for details.")
            return False

def main():
    """Main test execution"""
    tester = ERPTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()