import { Page, Card } from '../components/ui/PageComponents';

export function ModelValidation() {
  return (
    <Page
      title="Model Validation"
      subtitle="Backtesting, statistical diagnostics, and walk-forward validation"
    >
      <Card title="Module Status" subtitle="Implementation pending">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🚧</div>
          <h3 className="text-lg font-medium text-slate-300 mb-2">Model Validation</h3>
          <p className="text-slate-500">This module will be implemented in subsequent milestones.</p>
        </div>
      </Card>
    </Page>
  );
}