import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function DecisionCentre() {
  return <Page title="Decision Centre" subtitle="Policy controls and systematic position recommendations" eyebrow="Research workspace">
    <ModulePlaceholder name="Decision Centre" description="Policy controls and systematic position recommendations" code="DEC" focus={['Risk policies', 'Constraints', 'Recommendations']} />
  </Page>;
}
