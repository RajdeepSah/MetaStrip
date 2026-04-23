interface Props {
  risks: string[];
}

export function RiskList({ risks }: Props) {
  if (risks.length === 0) {
    return (
      <div className="flex items-center gap-2 font-mono text-sm text-risk-green py-1">
        <span>✓</span>
        <span>No risk factors detected</span>
      </div>
    );
  }

  return (
    <ul className="space-y-2">
      {risks.map((risk, i) => (
        <li key={i} className="flex items-start gap-3 font-mono text-sm">
          <span className="text-risk-amber mt-0.5 shrink-0 text-xs">▲</span>
          <span className="text-text-primary">{risk}</span>
        </li>
      ))}
    </ul>
  );
}
