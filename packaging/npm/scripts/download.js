#!/usr/bin/env node
// Postinstall hook — downloads the platform-appropriate standalone
// Quell binary from the matching GitHub release and caches it under
// ~/.cache/quell-npm/<version>/.
//
// This runs once at `npm install` time; afterwards `bin/quell.js`
// just spawns the cached binary.

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const https = require('https');
const { spawnSync } = require('child_process');
const zlib = require('zlib');
const { pipeline } = require('stream');

const pkg = require('../package.json');
const VERSION = pkg.version;
const REPO = 'bhartiyaanshul/quell';

const { platform, arch } = detectPlatform();
const assetName = `quell-${platform}-${arch}.tar.gz`;
const assetUrl =
  `https://github.com/${REPO}/releases/download/v${VERSION}/${assetName}`;

const cacheDir = path.join(
  process.env.QUELL_CACHE_DIR || path.join(os.homedir(), '.cache', 'quell-npm'),
  VERSION,
);
const binaryDir = path.join(cacheDir, 'quell');
const binaryPath = path.join(
  binaryDir,
  platform === 'Windows' ? 'quell.exe' : 'quell',
);

if (fs.existsSync(binaryPath)) {
  log(`Quell ${VERSION} already installed at ${binaryPath}`);
  process.exit(0);
}

fs.mkdirSync(cacheDir, { recursive: true });
const archivePath = path.join(cacheDir, assetName);

log(`Downloading Quell ${VERSION} (${platform}-${arch})…`);
log(`  ${assetUrl}`);

download(assetUrl, archivePath)
  .then(() => extract(archivePath, cacheDir))
  .then(() => {
    fs.chmodSync(binaryPath, 0o755);
    log(`Installed ${binaryPath}`);
  })
  .catch((err) => {
    console.error(`\nQuell install failed: ${err.message}\n`);
    console.error('You can alternatively install Quell directly:');
    console.error(
      '  curl -fsSL https://raw.githubusercontent.com/bhartiyaanshul/quell/main/install.sh | bash\n',
    );
    process.exit(1);
  });

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function detectPlatform() {
  let platform;
  switch (process.platform) {
    case 'darwin':
      platform = 'Darwin';
      break;
    case 'linux':
      platform = 'Linux';
      break;
    case 'win32':
      platform = 'Windows';
      break;
    default:
      throw new Error(`Unsupported platform: ${process.platform}`);
  }

  let arch;
  switch (process.arch) {
    case 'arm64':
      arch = 'arm64';
      break;
    case 'x64':
      arch = 'x86_64';
      break;
    default:
      throw new Error(`Unsupported arch: ${process.arch}`);
  }
  return { platform, arch };
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const go = (u, redirects) => {
      if (redirects > 5) {
        reject(new Error('Too many redirects'));
        return;
      }
      https
        .get(u, (res) => {
          if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
            go(res.headers.location, redirects + 1);
            return;
          }
          if (res.statusCode !== 200) {
            reject(new Error(`HTTP ${res.statusCode} for ${u}`));
            return;
          }
          const out = fs.createWriteStream(dest);
          pipeline(res, out, (err) => (err ? reject(err) : resolve()));
        })
        .on('error', reject);
    };
    go(url, 0);
  });
}

function extract(archivePath, destDir) {
  return new Promise((resolve, reject) => {
    // Prefer the system `tar` (universally available on macOS/Linux/WSL).
    const result = spawnSync('tar', ['-xzf', archivePath, '-C', destDir], {
      stdio: 'inherit',
    });
    if (result.error) {
      reject(result.error);
      return;
    }
    if (result.status !== 0) {
      reject(new Error(`tar exited with status ${result.status}`));
      return;
    }
    resolve();
  });
}

function log(msg) {
  if (process.env.QUELL_INSTALL_QUIET) return;
  console.error(`[quell-install] ${msg}`);
}
