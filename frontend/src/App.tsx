import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Dashboard } from './pages/Dashboard';
import { MarketData } from './pages/MarketData';
import { StatisticalAnalysis } from './pages/StatisticalAnalysis';
import { SimulationLab } from './pages/SimulationLab';
import { RiskLab } from './pages/RiskLab';
import { DecisionCentre } from './pages/DecisionCentre';
import { ModelValidation } from './pages/ModelValidation';
import { ResearchReports } from './pages/ResearchReports';
import { Layout } from './components/layout/Layout';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/market-data" element={<MarketData />} />
        <Route path="/statistical-analysis" element={<StatisticalAnalysis />} />
        <Route path="/simulation-lab" element={<SimulationLab />} />
        <Route path="/risk-lab" element={<RiskLab />} />
        <Route path="/decision-centre" element={<DecisionCentre />} />
        <Route path="/model-validation" element={<ModelValidation />} />
        <Route path="/research-reports" element={<ResearchReports />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;