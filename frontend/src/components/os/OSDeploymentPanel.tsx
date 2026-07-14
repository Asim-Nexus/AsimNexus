import { useState, useEffect } from 'react';
import api from '../../api/asimnexus';

const g = async (path: string): Promise<Record<string, unknown>> => { try { const r = await api.get(path); return r.data as Record<string, unknown>; } catch { return {}; } };
const p = async (path: string, data: Record<string, unknown>): Promise<Record<string, unknown>> => { try { const r = await api.post(path, data); return r.data as Record<string, unknown>; } catch { return {}; } };

export default function OSDeploymentPanel() {
    const [targets, setTargets] = useState<string[]>([]);
    const [, setStatus] = useState<Record<string, unknown>>({});
    const [releases, setReleases] = useState<unknown[]>([]);
    const [buildTarget] = useState('pwa');
    const [buildVersion, setBuildVersion] = useState('0.1.0');
    const [buildLoading, setBuildLoading] = useState(false);
    const [buildResult, setBuildResult] = useState<Record<string, unknown> | null>(null);

    useEffect(() => {
        g('/api/deploy/targets').then(res => { if ((res as Record<string, unknown>).targets) setTargets((res as Record<string, unknown>).targets as string[]); });
        g('/api/deploy/status').then(res => setStatus(res || {}));
        g('/api/deploy/releases?target=' + buildTarget).then(res => {
            setReleases(Array.isArray(res) ? res : (res && (res as Record<string, unknown>).releases ? (res as Record<string, unknown>).releases as unknown[] : []));
        });
    }, [buildTarget]);

    const handleBuild = async (e: React.FormEvent) => {
        e.preventDefault();
        setBuildLoading(true);
        try {
            const res = await p('/api/deploy/build', { target: buildTarget, version: buildVersion });
            setBuildResult((res as Record<string, unknown>).error ? { error: (res as Record<string, unknown>).error as string } : { success: true, message: 'Built ' + buildVersion });
        } catch (err) { setBuildResult({ error: (err as Error).message }); }
        setBuildLoading(false);
    };

    return (
        <div style={{ padding: 24 }}>
            <h2>OS Deployment</h2>
            <div style={{ marginBottom: 20 }}>Targets: {targets.length}</div>
            <form onSubmit={handleBuild}>
                <input value={buildVersion} onChange={e => setBuildVersion(e.target.value)} placeholder="Version" />
                <button type="submit" disabled={buildLoading}>Build</button>
            </form>
            {buildResult && <div>{(buildResult.message as string) || (buildResult.error as string)}</div>}
            <div>Releases: {releases.length}</div>
        </div>
    );
}
