import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Button } from './ui/button';
import { 
  Home, 
  Users, 
  Package, 
  DollarSign, 
  LogOut, 
  Menu,
  X,
  History,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

const Layout = ({ user, onLogout }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [financeiroOpen, setFinanceiroOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Clientes', href: '/clientes', icon: Users },
    { name: 'Produtos', href: '/produtos', icon: Package },
  ];

  const isActive = (href) => location.pathname === href;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-gray-600 bg-opacity-50 lg:hidden z-20"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-30 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex items-center justify-between h-16 px-6 border-b">
          <h1 className="text-xl font-bold text-gray-900">ERP System</h1>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="mt-6">
          <ul className="space-y-1 px-3">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive(item.href)
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
            
            {/* Menu Financeiro com submenu */}
            <li>
              <div>
                <button
                  onClick={() => setFinanceiroOpen(!financeiroOpen)}
                  className={`flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors text-left ${
                    location.pathname.startsWith('/financeiro')
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <DollarSign className="mr-3 h-5 w-5" />
                  Financeiro
                  {financeiroOpen ? (
                    <ChevronDown className="ml-auto h-4 w-4" />
                  ) : (
                    <ChevronRight className="ml-auto h-4 w-4" />
                  )}
                </button>
                
                {financeiroOpen && (
                  <ul className="mt-1 ml-6 space-y-1">
                    <li>
                      <Link
                        to="/financeiro"
                        className={`flex items-center px-3 py-2 text-sm rounded-md transition-colors ${
                          isActive('/financeiro')
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <DollarSign className="mr-3 h-4 w-4" />
                        Cadastro
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/financeiro/historico"
                        className={`flex items-center px-3 py-2 text-sm rounded-md transition-colors ${
                          isActive('/financeiro/historico')
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <History className="mr-3 h-4 w-4" />
                        Histórico
                      </Link>
                    </li>
                  </ul>
                )}
              </div>
            </li>
          </ul>
        </nav>
      </div>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="bg-white shadow-sm border-b">
          <div className="flex items-center justify-between px-6 h-16">
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>

            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Bem-vindo, <strong>{user?.username}</strong>
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={onLogout}
                className="flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Sair</span>
              </Button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;