import { Page, Card } from '../components/ui/PageComponents';

export function RiskLab() {
  return (
    <Page
      title="Risk Laboratory"
      subtitle="VaR, Expected Shortfall, drawdown, and risk decomposition"
    >
      <Card title="Module Status" subtitle="Implementation pending">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🚧</div>
          <h3 className="text-lg font-medium text-slate-300 mb-2">Risk Laboratory</h3>
          <p className="text-slate-500">This module will be implemented in subsequent milestones.</p>
        </div>
      </Card>
    </Page>
  );
}