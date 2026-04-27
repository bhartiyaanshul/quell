export default function SettingsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
      <p className="text-sm text-fg-muted">
        Quell reads its configuration from <code className="font-mono">.quell/config.toml</code>{" "}
        in your project directory and from the OS keychain for secrets.
        The dashboard is read-only; edit the file directly to change
        monitors, notifiers, and agent budgets.
      </p>
      <div className="rounded-2xl border border-border bg-bg-raised/40 p-6 text-sm text-fg-muted">
        <ul className="list-inside list-disc space-y-2">
          <li>
            Monitors, notifiers, and LLM config live in <code className="font-mono">.quell/config.toml</code>.
          </li>
          <li>
            API keys and webhook URLs live in the OS keychain.
          </li>
          <li>
            Per-investigation budget: <code className="font-mono">[agent]</code>{" "}
            <code className="font-mono">max_cost_usd</code>.
          </li>
        </ul>
      </div>
    </div>
  );
}
