import { Page, ModulePlaceholder } from '../components/ui/PageComponents';

export function ResearchReports() {
  return <Page title="Research Reports" subtitle="A considered record of research findings and model performance" eyebrow="Research workspace">
    <ModulePlaceholder name="Research Reports" description="A considered record of research findings and model performance" code="RPT" focus={['Portfolio notes', 'Model cards', 'Exports']} />
  </Page>;
}
