import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function ModelValidation() {
  return <Page title="Model Validation" subtitle="Backtests, diagnostics, and walk-forward model evaluation" eyebrow="Research workspace">
    <ModulePlaceholder name="Model Validation" description="Backtests, diagnostics, and walk-forward model evaluation" code="VAL" focus={['Backtesting', 'Diagnostics', 'Walk-forward']} />
  </Page>;
}
