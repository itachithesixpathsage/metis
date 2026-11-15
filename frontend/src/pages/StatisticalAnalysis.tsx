import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function StatisticalAnalysis() {
  return <Page title="Statistical Analysis" subtitle="Returns, distribution diagnostics, and rolling market behaviour" eyebrow="Research workspace">
    <ModulePlaceholder name="Statistical Analysis" description="Returns, distribution diagnostics, and rolling market behaviour" code="ST" focus={['Returns', 'Volatility', 'Correlation']} />
  </Page>;
}
