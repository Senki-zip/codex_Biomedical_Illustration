#!/usr/bin/env node
// Optional preview renderer. Core SVG creation uses only Python's standard library.
const fs = require('fs');
const path = require('path');
const os = require('os');
let sharp;
try { sharp = require('sharp'); } catch {
  const bundled = path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
  try { sharp = require(bundled); } catch {
    process.stderr.write('PNG rendering needs the optional sharp package. SVG output is already usable.\n');
    process.exit(1);
  }
}
const [source, output, widthString] = process.argv.slice(2);
if (!source || !output) {
  process.stderr.write('Usage: node render.cjs input.svg output.png [width=1800]\n');
  process.exit(1);
}
const width = Number(widthString || 1800);
if (!Number.isInteger(width) || width < 100 || width > 15000) throw new Error('Invalid output width');
fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
sharp(source, { density: 144 }).resize({ width }).png().toFile(output)
  .then(info => process.stdout.write(JSON.stringify({ output: path.resolve(output), ...info }) + '\n'))
  .catch(err => { process.stderr.write(err.message + '\n'); process.exit(1); });
