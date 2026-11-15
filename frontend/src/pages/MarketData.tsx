import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function MarketData() {
  return <Page title="Market Data" subtitle="Intraday FX market data acquisition, validation, and exploration" eyebrow="Research workspace">
    <ModulePlaceholder name="Market Data" description="Intraday FX market data acquisition, validation, and exploration" code="MD" focus={['Streaming quotes', 'Quality checks', 'Pair watchlist']} />
  </Page>;
}
