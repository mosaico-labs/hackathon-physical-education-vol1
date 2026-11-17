# hackathon-physical-education-vol1

Welcome! In this hackathon your team teaches an **SO-101** robot arm a task by showing it how
to do it. You record demonstrations with [LeRobot](https://github.com/huggingface/lerobot), train
a policy on it, and share your recordings with every other team through
[**Mosaico**](https://mosaico.dev).

You work on two computers:

- **Your laptop** is plugged into the arms. You record demonstrations on it and run the trained
  policy on it.
- **Your cloud machine** has a GPU. You train on it, and it's the only computer that can reach
  Mosaico, where every team shares their recordings.

Nothing here uses Hugging Face: datasets stay in the `data/` folder, trained policies in
`outputs/`, and the commands run LeRobot in offline mode, so it never contacts the Hugging Face Hub.

The repo has one folder per computer: **`laptop/`** and **`cloud/`**. Each has its own `justfile`
and `.env`, so on each computer you only see the commands that make sense there. Every command in
this guide is a `just` command, run from that folder; run `just` on its own to list them. The
commands are thin shortcuts over [LeRobot](https://huggingface.co/docs/lerobot) and the `mosaico`
CLI: use those directly whenever you need more. First install the software listed in
[PREREQUISITES.md](PREREQUISITES.md).

> [!IMPORTANT]
> **Images must be saved inside the dataset's parquet files, not as MP4 videos.** Mosaico can't
> read the videos, so a dataset recorded with them would reach Mosaico without its camera images.
> `just record` saves them correctly, and `just upload` and `just push` refuse a dataset that has
> videos. If you call `lerobot-record` yourself, add `--dataset.video=false`.

## On your laptop

### 1. Connect to your cloud machine

The organisers give your team the address of your cloud machine and a key file ending in
`.pem`. Here we call it `team.pem`; use the real name of your file.

1. Move the key to your ssh folder and make it readable only by you (ssh refuses keys that other
   users can read):

   ```bash
   mkdir -p ~/.ssh
   mv ~/Downloads/team.pem ~/.ssh/team.pem
   chmod 400 ~/.ssh/team.pem
   ```

2. Give the machine a short name. Open `~/.ssh/config` (create it if it doesn't exist) and add:

   ```
   Host hackathon
       HostName <address of your cloud machine>
       User ubuntu
       IdentityFile ~/.ssh/team.pem
   ```

3. Check it works:

   ```bash
   ssh hackathon
   ```

   The first time, ssh asks whether you trust the machine: type `yes`. You should end up in a
   shell on the cloud machine. Type `exit` to come back.

From now on `ssh hackathon` opens a shell on the cloud machine, and the commands of this repo use
the same name to copy files.

### 2. Set up the repo

```bash
git clone https://github.com/mosaico-labs/hackathon-physical-education-vol1.git
cd hackathon-physical-education-vol1/laptop
just setup
```

This installs LeRobot in a local `.venv` and creates a `.env` file, which you fill in in the next
step. All the laptop commands below run from the `laptop/` folder.

### 3. Prepare the arms

You have two arms: the **leader**, which you move by hand, and the **follower**, which copies it.

```bash
just find-port               # tells you which USB port each arm is on: put them in .env
just find-cameras            # lists the cameras: put the one you want in CAMERAS in .env
just calibrate follower      # once per arm, follow the instructions on screen
just calibrate leader
just teleop                  # move the leader and check that the follower follows
```

Brand new arms that were never configured also need `just setup-motors follower` and
`just setup-motors leader` before calibrating.

### 4. Record demonstrations

```bash
just record pick "Pick up the red cube" 10
```

This records 10 demonstrations (episodes) of the task into `data/pick`. For each episode you have
60 seconds to do the task with the leader arm, then 60 seconds to put the scene back. Describe
the task in a plain sentence: it's saved with the recordings.

To add episodes to an existing dataset later, add `--resume=true`. Any other
[LeRobot option](https://huggingface.co/docs/lerobot) can be added the same way, for example
`--dataset.episode_time_s=30`.

To watch an episode you recorded:

```bash
just viz pick 0
```

### 5. Send your recordings to the cloud machine

```bash
just upload pick
```

This copies `data/pick` to the cloud machine (set up the repo there first, see
[step 1 on the cloud machine](#1-set-up-the-repo-1)). Continue on the cloud machine with
[On the cloud machine](#on-the-cloud-machine), then come back here once a training run is done.

### 6. Bring back a trained policy and run it

Training saves everything in a folder under `outputs/train/` on the cloud machine. Copy the one
you want to your laptop:

```bash
just pull outputs/train/pick_act       # → outputs/pulled/pick_act
```

Then let the trained policy drive the follower arm (stop it with `Ctrl+C`):

```bash
just rollout outputs/pulled/pick_act "Pick up the red cube"
```

## On the cloud machine

Open a shell on it from your laptop with `ssh hackathon`.

### 1. Set up the repo

```bash
git clone https://github.com/mosaico-labs/hackathon-physical-education-vol1.git
cd hackathon-physical-education-vol1/cloud
just setup
```

This installs LeRobot (for training) in a local `.venv` and creates a `.env` file. Mosaico is used
through the `mosaico` CLI that is already installed on the machine. Open `.env`, set `TEAM` to
your team name (it must be unique: it's how your recordings are told apart in Mosaico) and
`MOSAICO_HOST` to the Mosaico address given by the organisers. Then save that address as your
`mosaico` profile and check that Mosaico answers:

```bash
just connect
```

All the cloud commands below run from the `cloud/` folder.

### 2. Share your recordings on Mosaico

Once you've sent a dataset from your laptop with `just upload pick`:

```bash
just push pick
```

Each episode becomes a sequence in Mosaico called `<TEAM>_pick_episode_000000`,
`<TEAM>_pick_episode_000001`, and so on, tagged with your team name. Add `--dry-run` to see what
would be sent without sending it.

### 3. Get recordings from Mosaico

Mosaico holds the recordings of every team. Browse them with the `mosaico` CLI, then rebuild a
LeRobot dataset from the ones you want, mixing your recordings with other teams':

```bash
mosaico sequence ls                                   # every sequence in Mosaico
mosaico sequence ls --locator "team-07_*"             # only team-07's
mosaico sequence ls -m team=team-07 -m dataset=pick   # by the metadata `just push` adds
mosaico sequence stat team-07_pick_episode_000000     # details of one sequence
just extract picks --locator "team-07_pick_*"         # rebuild them as a dataset in data/picks
```

`just extract` takes the same filters as `mosaico sequence ls`. Run `mosaico --help` to see
everything the CLI can do.

### 4. Train a policy

```bash
just train pick act 20000
```

This trains an [ACT](https://huggingface.co/docs/lerobot/act) policy for 20 000 steps on
`data/pick` and saves it in `outputs/train/pick_act`. Training takes a while: start it inside
`tmux` (`tmux new -s train`) so it keeps running if your connection drops. Reconnect to it later
with `tmux attach -t train`.

When it's done, go back to your laptop and [bring the policy back](#6-bring-back-a-trained-policy-and-run-it).

## Going further

The `just` commands only fill in the options for this setup. Run the tools directly for anything
else: `mosaico --help`, `mosaicolabs.lerobot_injector --help`, `mosaicolabs.lerobot_extractor --help`
and the LeRobot `lerobot-*` commands (`uv run lerobot-train --help`). To learn more about Mosaico,
see [mosaico.dev](https://mosaico.dev). The Mosaico server used in this hackathon is
[`mosaicod`](https://github.com/mosaico-labs/mosaicod).
