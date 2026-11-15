import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function RiskLab() {
  return <Page title="Risk Laboratory" subtitle="Portfolio loss estimates, drawdown, and component risk" eyebrow="Research workspace">
    <ModulePlaceholder name="Risk Laboratory" description="Portfolio loss estimates, drawdown, and component risk" code="RSK" focus={['VaR / ES', 'Drawdown', 'Attribution']} />
  </Page>;
}
