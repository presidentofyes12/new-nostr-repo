const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');
const unzipper = require('unzipper');

const app = express();
app.use(express.json());

const REPO_URL = 'https://github.com/scsibug/nostr-rs-relay/archive/refs/heads/master.zip';
const RELAY_DIR = path.join(__dirname, 'nostr-rs-relay');

app.post('/api/setup-relay', async (req, res) => {
  const { port, nostrKey } = req.body;

  if (!port || !nostrKey) {
    return res.status(400).json({ success: false, error: 'Port and Nostr private key are required' });
  }

  try {
    // Step 1: Download and extract nostr-rs-relay
    await downloadAndExtractRelay();

    // Step 2: Build and set up the relay
    await buildAndSetupRelay(port);

    // Step 3: Set up noscl
    await setupNoscl(nostrKey, port);

    res.json({ success: true, message: 'Nostr relay and OpenVPN setup completed successfully' });
  } catch (error) {
    console.error('Setup failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

async function downloadAndExtractRelay() {
  console.log('Downloading nostr-rs-relay...');
  const response = await axios({
    method: 'get',
    url: REPO_URL,
    responseType: 'stream'
  });

  await new Promise((resolve, reject) => {
    response.data.pipe(unzipper.Extract({ path: __dirname }))
      .on('close', () => {
        fs.renameSync(path.join(__dirname, 'nostr-rs-relay-master'), RELAY_DIR);
        resolve();
      })
      .on('error', reject);
  });

  console.log('nostr-rs-relay downloaded and extracted');
}

function buildAndSetupRelay(port) {
  return new Promise((resolve, reject) => {
    const commands = [
      'podman build --pull -t nostr-rs-relay .',
      'mkdir -p data',
      `podman run -d -p ${port}:8080 --user=100:100 -v $(pwd)/data:/usr/src/app/db:Z -v $(pwd)/config.toml:/usr/src/app/config.toml:ro,Z --name nostr-relay nostr-rs-relay:latest`
    ];

    const executeCommands = (index) => {
      if (index >= commands.length) {
        resolve();
        return;
      }

      exec(commands[index], { cwd: RELAY_DIR }, (error, stdout, stderr) => {
        if (error) {
          console.error(`Error executing command: ${commands[index]}`);
          console.error(stderr);
          reject(error);
          return;
        }
        console.log(stdout);
        executeCommands(index + 1);
      });
    };

    executeCommands(0);
  });
}

function setupNoscl(nostrKey, port) {
  return new Promise((resolve, reject) => {
    const commands = [
      `noscl setprivate ${nostrKey}`,
      `noscl relay add ws://localhost:${port}`
    ];

    const executeCommands = (index) => {
      if (index >= commands.length) {
        resolve();
        return;
      }

      exec(commands[index], (error, stdout, stderr) => {
        if (error) {
          console.error(`Error executing command: ${commands[index]}`);
          console.error(stderr);
          reject(error);
          return;
        }
        console.log(stdout);
        executeCommands(index + 1);
      });
    };

    executeCommands(0);
  });
}

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));