/**
 * Nepal Hub — Digital Nepal Governance
 * All tabs wired to real components with live API data
 * Tab labels auto-translate via i18n system (en/ne/hi)
 */
import SmartHub from '../shared/SmartHub';
import NepalDashboard from '../nepal/NepalDashboard';
import EResidencyFlow from '../nepal/EResidencyFlow';
import TaxFilingPanel from '../nepal/TaxFilingPanel';
import NepaliLanguageSelector from '../nepal/NepaliLanguageSelector';
import NepalPaymentGateway from '../nepal/NepalPaymentGateway';
import NepalDigitalIdentity from '../nepal/NepalDigitalIdentity';
import { useI18n } from '../../i18n';

interface NepalHubProps {
    user?: Record<string, unknown>;
}

export default function NepalHub({ user }: NepalHubProps) {
    const { t } = useI18n();

    const TABS = [
        { id: 'dashboard', label: t('nepal_hub.tabs.dashboard'), icon: '🇳🇵', desc: t('nepal_hub.tab_descs.dashboard') },
        { id: 'identity', label: t('nepal_hub.tabs.identity'), icon: '🆔', desc: t('nepal_hub.tab_descs.identity') },
        { id: 'payment', label: t('nepal_hub.tabs.payment'), icon: '💳', desc: t('nepal_hub.tab_descs.payment') },
        { id: 'eresidency', label: t('nepal_hub.tabs.eresidency'), icon: '🪪', desc: t('nepal_hub.tab_descs.eresidency') },
        { id: 'tax', label: t('nepal_hub.tabs.tax'), icon: '💰', desc: t('nepal_hub.tab_descs.tax') },
        { id: 'language', label: t('nepal_hub.tabs.language'), icon: '🌐', desc: t('nepal_hub.tab_descs.language') },
    ];

    return (
        <SmartHub
            tabs={TABS}
            title={t('nepal_hub.title')}
            icon="🇳🇵"
            accentColor="#c9a84c"
        >
            {(tab) => {
                switch (tab.id) {
                    case 'dashboard':
                        return <NepalDashboard user={user} />;
                    case 'identity':
                        return <NepalDigitalIdentity user={user} />;
                    case 'payment':
                        return <NepalPaymentGateway user={user} />;
                    case 'eresidency':
                        return <EResidencyFlow user={user} />;
                    case 'tax':
                        return <TaxFilingPanel user={user} />;
                    case 'language':
                        return <NepaliLanguageSelector />;
                    default:
                        return <div style={{ color: '#94a3b8', padding: 20 }}>{t('app.no_data')}</div>;
                }
            }}
        </SmartHub>
    );
}
