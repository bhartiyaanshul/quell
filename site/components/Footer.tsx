export default function Footer() {
  return (
    <footer className="py-10 px-6 border-t border-va-border bg-va-bg-alt">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-5">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <span className="text-va-accent text-lg">&#x27C1;</span>
          <span className="font-bold tracking-tight">frisk</span>
          <span className="text-va-faint text-xs ml-1">v0.1.0</span>
        </div>

        {/* Links */}
        <div className="flex items-center gap-6 text-sm text-va-muted">
          <a
            href="https://github.com/Bhartiyaanshul/frisk"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-va-text transition-colors duration-200"
          >
            GitHub
          </a>
          <a
            href="https://x.com/Bhartiyaanshul"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-va-text transition-colors duration-200"
          >
            Twitter
          </a>
          <a
            href="https://linkedin.com/in/anshulbhartiya"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-va-text transition-colors duration-200"
          >
            LinkedIn
          </a>
        </div>

        {/* Credit */}
        <div className="text-sm text-va-faint">
          MIT &middot; Built by{" "}
          <a
            href="https://anshulbuilds.xyz"
            target="_blank"
            rel="noopener noreferrer"
            className="text-va-muted hover:text-va-text transition-colors duration-200"
          >
            Anshul Bhartiya
          </a>
        </div>
      </div>
    </footer>
  );
}
