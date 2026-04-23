interface Props {
  score: number;
}

export function SensitivityRing({ score }: Props) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score < 30 ? "#00cc88" : score < 70 ? "#ffaa00" : "#ff4444";
  const label =
    score < 30 ? "Low Risk" : score < 70 ? "Medium Risk" : "High Risk";

  return (
    <div className="flex flex-col items-center gap-2 shrink-0">
      <div className="relative w-32 h-32">
        <svg width="128" height="128" viewBox="0 0 128 128">
          <circle
            cx="64"
            cy="64"
            r={radius}
            fill="none"
            stroke="#1e2d3a"
            strokeWidth="10"
          />
          <circle
            cx="64"
            cy="64"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 64 64)"
            style={{ transition: "stroke-dashoffset 0.7s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono text-3xl font-semibold leading-none"
            style={{ color }}
          >
            {score}
          </span>
          <span className="font-mono text-[10px] text-text-muted mt-1">
            / 100
          </span>
        </div>
      </div>
      <span
        className="font-mono text-xs font-medium"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  );
}
