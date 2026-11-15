import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function SimulationLab() {
  return <Page title="Simulation Laboratory" subtitle="Scenario generation across stochastic and resampling models" eyebrow="Research workspace">
    <ModulePlaceholder name="Simulation Laboratory" description="Scenario generation across stochastic and resampling models" code="SIM" focus={['GBM paths', 'Historical bootstrap', 'GARCH']} />
  </Page>;
}
