#!/usr/bin/env node
// Entry point that npm wires onto the user's PATH as `quell`.
//
// All this does is spawn the real binary that was downloaded at
// `npm install` time (see scripts/download.js).  It mirrors the exit
// code and signal handling so `quell` behaves identically to the
// native binary.

'use strict';

const os = require('os');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const pkg = require('../package.json');
const VERSION = pkg.version;

const cacheDir = path.join(
  process.env.QUELL_CACHE_DIR || path.join(os.homedir(), '.cache', 'quell-npm'),
  VERSION,
);
const isWindows = process.platform === 'win32';
const binaryPath = path.join(
  cacheDir,
  'quell',
  isWindows ? 'quell.exe' : 'quell',
);

if (!fs.existsSync(binaryPath)) {
  console.error(
    `Quell binary not found at ${binaryPath}.\n` +
      'Re-run `npm install -g quell-agent` to fetch it, or install via ' +
      'curl:\n\n' +
      '  curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash\n',
  );
  process.exit(1);
}

const child = spawn(binaryPath, process.argv.slice(2), {
  stdio: 'inherit',
  windowsHide: true,
});

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

// Forward common termination signals to the child.
for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
  process.on(sig, () => {
    if (!child.killed) child.kill(sig);
  });
}
