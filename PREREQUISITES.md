# Prerequisites

Software to install before using this repo. Once it's installed, go back to the [README](README.md).

## On your laptop

| Software | How to install |
|----------|----------------|
| git | preinstalled on macOS and most Linux distributions |
| [uv](https://docs.astral.sh/uv/) (Python and its packages) | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv` |
| [just](https://just.systems) (runs the commands of this repo) | `brew install just` or `uv tool install rust-just` |
| ssh and rsync (talk to the cloud machine) | preinstalled on macOS and Linux |

The SO-101 arms connect over USB: on Linux, add yourself to the `dialout` group
(`sudo usermod -aG dialout $USER`, then log out and back in) so you can open the serial ports.

## On the cloud machine

| Software | How to install |
|----------|----------------|
| git, uv, just | same commands as above |
| NVIDIA driver and CUDA | already installed on the hackathon machines (check with `nvidia-smi`) |
| `mosaico` CLI and the Mosaico LeRobot bridge (`mosaicolabs.lerobot_injector`, `mosaicolabs.lerobot_extractor`) | already installed on the hackathon machines (check with `mosaico --help`) |
